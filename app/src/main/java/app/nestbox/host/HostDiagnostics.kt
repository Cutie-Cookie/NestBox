package app.nestbox.host

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.os.PowerManager
import java.io.File
import java.util.Locale

/**
 * Read-only host snapshot for diagnosing the rootless Android guest.
 *
 * Android may restrict individual procfs/sysfs files. Every probe is best-effort and explicitly
 * marked unavailable rather than inferring a value from the device model or advertised RAM.
 */
object HostDiagnostics {
    fun snapshot(context: Context): String = buildString {
        val am = context.getSystemService(ActivityManager::class.java)
        val mi = ActivityManager.MemoryInfo()
        am.getMemoryInfo(mi)

        appendLine("NapBox host runtime diagnostics")
        appendLine("timestamp_ms=${System.currentTimeMillis()}")
        appendLine("device=${Build.MANUFACTURER} ${Build.MODEL}")
        appendLine("hardware=${Build.HARDWARE}")
        appendLine("soc_model=${if (Build.VERSION.SDK_INT >= 31) Build.SOC_MODEL else "unavailable (API < 31)"}")
        appendLine("android_release=${Build.VERSION.RELEASE}")
        appendLine("sdk=${Build.VERSION.SDK_INT}")
        appendLine("supported_abis=${Build.SUPPORTED_ABIS.joinToString(",")}")
        appendLine()
        appendLine("[memory]")
        appendLine("total_bytes=${mi.totalMem}")
        appendLine("available_bytes=${mi.availMem}")
        appendLine("threshold_bytes=${mi.threshold}")
        appendLine("low_memory=${mi.lowMemory}")
        appendLine("proc_meminfo:\n${read("/proc/meminfo")}")
        appendLine()
        appendLine("[cpu]")
        appendLine("online=${read("/sys/devices/system/cpu/online")}")
        appendLine("present=${read("/sys/devices/system/cpu/present")}")
        appendLine("possible=${read("/sys/devices/system/cpu/possible")}")
        appendLine("process_status:\n${selectedLines(read("/proc/self/status"), listOf("Name:", "Threads:", "Cpus_allowed:", "Cpus_allowed_list:"))}")
        val cpuRoot = File("/sys/devices/system/cpu")
        val cores = cpuRoot.listFiles()?.filter { it.name.matches(Regex("cpu[0-9]+")) }?.sortedBy { it.name } ?: emptyList()
        for (core in cores) {
            val topology = listOf("topology/core_id", "topology/physical_package_id", "topology/thread_siblings_list", "cpu_capacity")
                .joinToString(" ") { path -> "$path=${read(File(core, path).path)}" }
            appendLine("${core.name}: $topology")
        }
        val policies = File("/sys/devices/system/cpu/cpufreq").listFiles()
            ?.filter { it.name.startsWith("policy") }?.sortedBy { it.name } ?: emptyList()
        for (policy in policies) {
            appendLine("${policy.name}: " + listOf(
                "related_cpus", "affected_cpus", "scaling_governor", "scaling_min_freq",
                "scaling_max_freq", "scaling_cur_freq", "cpuinfo_max_freq"
            ).joinToString(" ") { path -> "$path=${read(File(policy, path).path)}" })
        }
        appendLine()
        appendLine("[process_and_cgroups]")
        appendLine("self_cgroup:\n${read("/proc/self/cgroup")}")
        appendLine("cpu_pressure:\n${read("/proc/pressure/cpu")}")
        appendLine("memory_pressure:\n${read("/proc/pressure/memory")}")
        val cgroupFiles = listOf(
            "cpu.max", "cpu.stat", "cpu.cfs_quota_us", "cpu.cfs_period_us",
            "cpuset.cpus", "cpuset.cpus.effective", "memory.max", "memory.current",
            "memory.high", "memory.events", "memory.limit_in_bytes", "memory.usage_in_bytes"
        )
        val paths = linkedSetOf("/sys/fs/cgroup")
        read("/proc/self/cgroup").lineSequence().forEach { line ->
            val rel = line.substringAfterLast(':', "").trim().trim('/')
            if (rel.isNotEmpty() && !rel.split('/').contains("..")) paths += "/sys/fs/cgroup/$rel"
        }
        for (base in paths) {
            for (name in cgroupFiles) {
                val value = read("$base/$name")
                if (value != UNAVAILABLE) appendLine("$base/$name=$value")
            }
        }
        appendLine()
        appendLine("[thermal]")
        val pm = context.getSystemService(PowerManager::class.java)
        if (Build.VERSION.SDK_INT >= 29) {
            appendLine("thermal_status=${runCatching { pm.currentThermalStatus }.getOrNull() ?: UNAVAILABLE}")
        } else appendLine("thermal_status=unavailable (API < 29)")
        appendLine("thermal_status_names=0 none, 1 light, 2 moderate, 3 severe, 4 critical, 5 emergency, 6 shutdown")
        val zones = File("/sys/class/thermal").listFiles()
            ?.filter { it.name.startsWith("thermal_zone") }?.sortedBy { it.name } ?: emptyList()
        for (zone in zones.take(16)) {
            appendLine("${zone.name}: type=${read(File(zone, "type").path)} temp_millidegrees=${read(File(zone, "temp").path)}")
        }
        appendLine("battery_temperature_c=${runCatching {
            val intent = context.registerReceiver(null, android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED))
            (intent?.getIntExtra(android.os.BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1).let { if (it >= 0) String.format(Locale.ROOT, "%.1f", it / 10.0) else UNAVAILABLE }
        }.getOrDefault(UNAVAILABLE)}")
    }

    private fun selectedLines(text: String, prefixes: List<String>): String =
        text.lineSequence().filter { line -> prefixes.any(line::startsWith) }.joinToString("\n").ifBlank { UNAVAILABLE }

    private fun read(path: String): String = runCatching {
        val file = File(path)
        if (file.isFile && file.canRead()) file.readText().trim().ifBlank { UNAVAILABLE } else UNAVAILABLE
    }.getOrDefault(UNAVAILABLE)

    private const val UNAVAILABLE = "unavailable/restricted"
}
