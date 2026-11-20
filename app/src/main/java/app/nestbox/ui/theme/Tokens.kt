package app.nestbox.ui.theme

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Design tokens from design/README.md §4. Keep values exact.
 * OKLCH colors are converted to sRGB hex (the README's "≈" hex values are rounder approximations).
 */
object Nb {
    // Backgrounds
    val Bg = Color(0xFF101010)
    val BgDeep = Color(0xFF090909)
    val Console = Color(0xFF050505)

    // Surfaces
    val Surface = Color(0xFF1D1D1D)
    val Surface2 = Color(0xFF292929)
    val Surface3 = Color(0xFF343434)
    val Hover = Color(0xFF252525)
    val Divider = Color(0xFF303030)
    val Outline = Color(0xFF555555)

    // Text
    val Text = Color(0xFFECEDEE)
    val Text2 = Color(0xFFC8C8C8)
    val Text3 = Color(0xFF999999)
    val Text4 = Color(0xFF707070)

    // Accent
    val Accent = Color(0xFFF2F2F2)
    val OnAccent = Color(0xFF101010)
    val AccentContainer = Color(0xFF3A3A3A)

    // Status
    val Amber = Color(0xFFB0B0B0)        // oklch(0.82 0.13 75)
    val Green = Color(0xFFBDBDBD)
    val Red = Color(0xFFD0D0D0)          // oklch(0.72 0.14 25)
    val PoweredOff = Color(0xFF5B5E63)

    // Component-specific values used in the design
    val ChipBg = Color(0xFF303030)
    val ChipText = Color(0xFFD0D0D0)
    val BannerBg = Color(0xFF292929)     // oklch(0.3 0.05 75)
    val BannerFg = Color(0xFFE0E0E0)     // oklch(0.88 0.12 75)
    val BannerSub = Color(0xFFBDBDBD)
    val BannerOnFg = Color(0xFF101010)
    val BetaTag = Color(0xFFC8C8C8)      // oklch(0.85 0.12 75)
    val HealthChip = Color(0xFF181818)
    val ConsoleText = Color(0xFFBDBDBD)
    val ConsoleTrack = Color(0xFF242424)
    val SegmentActive = Color(0xFF454545)
    val Stripe1 = Color(0xFF202020)
    val Stripe2 = Color(0xFF2A2A2A)
    val GuestStripe1 = Color(0xFF151515)
    val GuestStripe2 = Color(0xFF1A1A1A)
    val MapBg = Color(0xFF191919)
    val MapLine = Color(0xFF222222)
    val FloatHome = Color(0xFF1B1B1B)
    val FloatIcon = Color(0xFF2B2B2B)
    val BallBg = Color(0xEBF2F2F2)       // rgba(76,141,255,.92)
    val BallMenu = Color(0xF71D1D1D)     // rgba(27,31,39,.97)
    val CoordsChip = Color(0xD9090909)   // rgba(10,12,16,.85)
    val JoyBg = Color(0xD91D1D1D)        // rgba(27,31,39,.85)
    val ToggleOffTrack = Outline
    val ToastBg = Text
    val ToastText = Bg

    // Radius
    val RPill = 999.dp
    val R24 = 24.dp
    val R20 = 20.dp
    val R16 = 16.dp
    val R12 = 12.dp
    val R8 = 8.dp
    val R6 = 6.dp

    // Type scale
    val T28 = 28.sp
    val T26 = 26.sp
    val T24 = 24.sp
    val T16 = 16.sp
    val T15 = 15.sp
    val T14 = 14.sp
    val T13_5 = 13.5.sp
    val T13 = 13.sp
    val T12_5 = 12.5.sp
    val T12 = 12.sp
    val T11_5 = 11.5.sp
    val T11 = 11.sp
    val T10_5 = 10.5.sp
    val T10 = 10.sp

    val Touch = 44.dp
}
