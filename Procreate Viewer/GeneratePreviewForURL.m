#include <CoreFoundation/CoreFoundation.h>
#include <CoreServices/CoreServices.h>
#include <QuickLook/QuickLook.h>
#import <Foundation/Foundation.h>
#import <Cocoa/Cocoa.h>

OSStatus GeneratePreviewForURL(void *thisInterface, QLPreviewRequestRef preview, CFURLRef url, CFStringRef contentTypeUTI, CFDictionaryRef options);
void CancelPreviewGeneration(void *thisInterface, QLPreviewRequestRef preview);

/* -----------------------------------------------------------------------------
   Generate a preview for file

   This function's job is to create preview for designated file
   ----------------------------------------------------------------------------- */

OSStatus GeneratePreviewForURL(void *thisInterface, QLPreviewRequestRef preview, CFURLRef url, CFStringRef contentTypeUTI, CFDictionaryRef options)
{
    // To complete your generator please implement the function GeneratePreviewForURL in GeneratePreviewForURL.c
    @autoreleasepool {
        NSURL *URL = (__bridge NSURL *)url;
        
        NSString *filename = [[URL absoluteString] lastPathComponent];
        NSArray *filename_array = [filename componentsSeparatedByString:@"."];
        NSString *file_extension = [filename_array lastObject];
        
        if ([file_extension isEqualToString:@"procreate"]) {
            NSTask *task = [[NSTask alloc] init];
            CFBundleRef bundle = QLPreviewRequestGetGeneratorBundle(preview);
            CFURLRef scriptURL = CFBundleCopyResourceURL(bundle, CFSTR("ProcreateImageData"), NULL, NULL);
            
            NSString *script = [(__bridge NSURL*)scriptURL path];
            
            [task setLaunchPath:script];
            [task setStandardInput: [NSPipe pipe]];
            [task setStandardOutput: [NSPipe pipe]];
            [task setArguments:@[[URL path]]];
            [task launch];
            [task waitUntilExit];
            
            
            NSString *user = NSUserName();
            NSString *pathtotemp = [NSString stringWithFormat:@"%@/%@/%@", @"/Users/", user, @"/.procreatetemp.bmp"];
            NSImage *image = [[NSImage alloc]initWithContentsOfFile:pathtotemp];
            CGImageSourceRef source;
            source = CGImageSourceCreateWithData((CFDataRef)[image TIFFRepresentation], NULL);
            CGImageRef maskRef =  CGImageSourceCreateImageAtIndex(source, 0, NULL);
            
            
            CGSize size = CGSizeMake(CGImageGetWidth(maskRef), CGImageGetHeight(maskRef));
            CGContextRef ctxt = QLPreviewRequestCreateContext(preview, size, YES, nil);
            CGContextDrawImage(ctxt, CGRectMake(0, 0, size.width, size.height), maskRef);
            QLPreviewRequestFlushContext(preview, ctxt);
            CGContextRelease(ctxt);
            [[NSFileManager defaultManager] removeItemAtPath: pathtotemp error: nil];
        }
    }

    return noErr;
}

void CancelPreviewGeneration(void *thisInterface, QLPreviewRequestRef preview)
{
    // Implement only if supported
}
