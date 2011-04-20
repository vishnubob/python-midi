#include <CoreFoundation/CoreFoundation.h>

CFStringRef uppercase(CFStringRef s)
{
  CFLocaleRef localeRef = CFLocaleCopyCurrent();

  CFMutableStringRef ms = CFStringCreateMutableCopy(NULL, 0, s);
  CFStringUppercase(ms, localeRef);

  CFRelease(localeRef);

  return ms;
}
