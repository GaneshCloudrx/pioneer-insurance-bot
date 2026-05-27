Add-Type @"
using System;
using System.Runtime.InteropServices;

public class Resolution {
  [DllImport("user32.dll")]
  public static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);

  [StructLayout(LayoutKind.Sequential)]
  public struct DEVMODE {
    public short dmSize;
    public int dmPelsWidth;
    public int dmPelsHeight;
  }

  public static void Set(int width, int height) {
    DEVMODE dm = new DEVMODE();
    dm.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
    dm.dmPelsWidth = width;
    dm.dmPelsHeight = height;
    ChangeDisplaySettings(ref dm, 0);
  }
}
"@

[Resolution]::Set(1920,1080)
