/* File : example.i */
%module example

%{
#include <CoreFoundation/CoreFoundation.h>
%}

%typemap(in) CFStringRef {
   if (!PyString_Check($input)) {
       PyErr_SetString(PyExc_ValueError, "Expecting a string");
       return NULL;
   }
   $1 = CFStringCreateWithCString(NULL, PyString_AsString($input), kCFStringEncodingASCII);
}

%typemap(freearg) CFStringRef {
  CFRelease($1);
}

%typemap(arginit) CFStringRef {
  $1 = NULL;
}

%typemap(out) CFStringRef {
  unsigned int len = CFStringGetLength($1);
  char *buffer = malloc(len + 1);
  if (CFStringGetCString($1, buffer, len + 1, kCFStringEncodingASCII)) {
    $result = PyString_FromStringAndSize(buffer, len);
    free(buffer);
    CFRelease($1);
  }
  else {
    PyErr_SetString(PyExc_ValueError, "Can't convert string");
    CFRelease($1);
    return NULL;
  }
}

extern CFStringRef uppercase(CFStringRef s);
