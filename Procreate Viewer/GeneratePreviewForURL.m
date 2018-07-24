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

CGPoint getSwatchPreviewPosition(int index) {
    int column = index % 10;
    int row = (int)floor(index / 10);
    CGPoint position = CGPointMake((column * 42), 84 - (row * 42));
    return position;
}

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
            
            NSURL               *fileurl = [NSURL fileURLWithPath:pathtotemp];
            CGImageRef          previewImage = NULL;
            CGImageSourceRef    previewImageSource;
            
            previewImageSource = CGImageSourceCreateWithURL((CFURLRef)fileurl, NULL);
            
            previewImage = CGImageSourceCreateImageAtIndex(previewImageSource, 0, NULL);
            CFRelease(previewImageSource);
            
            CGSize size = CGSizeMake(CGImageGetWidth(previewImage), CGImageGetHeight(previewImage));
            CGContextRef ctxt = QLPreviewRequestCreateContext(preview, size, YES, nil);
            CGContextDrawImage(ctxt, CGRectMake(0, 0, size.width, size.height), previewImage);
            QLPreviewRequestFlushContext(preview, ctxt);
            CGContextRelease(ctxt);
            //[[NSFileManager defaultManager] removeItemAtPath: pathtotemp error: nil];
        }
        else if ([file_extension isEqualToString:@"brush"]) {
            
            NSData *thumbdata = nil;
            
            NSTask *unzipTask = [NSTask new];
            [unzipTask setLaunchPath:@"/usr/bin/unzip"];
            [unzipTask setStandardOutput:[NSPipe pipe]];
            [unzipTask setArguments:@[@"-p", [URL path], @"QuickLook/Thumbnail.png"]];
            [unzipTask launch];
            
            thumbdata = [[[unzipTask standardOutput] fileHandleForReading] readDataToEndOfFile];
            NSBitmapImageRep * image = [NSBitmapImageRep imageRepWithData:thumbdata];
            
            CGImageRef imageref = image.CGImage;
            
            CGSize size = CGSizeMake(CGImageGetWidth(imageref), CGImageGetHeight(imageref));
            CGContextRef ctxt = QLPreviewRequestCreateContext(preview, size, YES, nil);
 
            NSString *osxMode = [[NSUserDefaults standardUserDefaults] stringForKey:@"AppleInterfaceStyle"];
            
            if ([osxMode isEqualToString:@"Dark"]) {
                // Show Normal preview (Black BG) if macOS dark mode is active
                CGContextSetRGBFillColor(ctxt, 0, 0, 0, 1);
                CGContextFillRect(ctxt, (CGRect){CGPointZero, size});
                CGContextDrawImage(ctxt, CGRectMake(0, 0, size.width, size.height), imageref);
            }
    
            else {
                // Invert color (White BG) if macOS dark mode is inactive
                CGContextSetRGBFillColor(ctxt, 1, 1, 1, 1);
                CGContextFillRect(ctxt, (CGRect){CGPointZero, size});
                CGContextSetRGBFillColor(ctxt, 0, 0, 0, 1);
                CGContextClipToMask(ctxt, CGRectMake(0, 0, size.width, size.height), imageref);
                CGContextFillRect(ctxt, (CGRect){CGPointZero, size});
            }
                
            QLPreviewRequestFlushContext(preview, ctxt);
            CGContextRelease(ctxt);
        }
        
        else if ([file_extension isEqual: @"brushset"]) {
            NSTask *unzipTask = [NSTask new];
            [unzipTask setLaunchPath:@"/usr/bin/unzip"];
            [unzipTask setStandardOutput:[NSPipe pipe]];
            [unzipTask setArguments:@[@"-p", [URL path], @"brushset.plist"]];
            [unzipTask launch];
            
            NSData *thumbdata = nil;
            
            thumbdata = [[[unzipTask standardOutput] fileHandleForReading] readDataToEndOfFile];
            NSError *error = nil;
            NSDictionary *plistdict = [NSPropertyListSerialization propertyListWithData:thumbdata options:NSPropertyListImmutable format:NULL error:&error];
            
            NSArray *brusheslist = [plistdict objectForKey:@"brushes"];
            
            NSDictionary *properties;
            CGSize thumbsize = CGSizeMake(860, 600);
            CGContextRef ctxt = QLPreviewRequestCreateContext(preview, thumbsize, true, (__bridge CFDictionaryRef)(properties));
            
            NSString *osxMode = [[NSUserDefaults standardUserDefaults] stringForKey:@"AppleInterfaceStyle"];
            
            if ([osxMode isEqualToString:@"Dark"]) {
                CGContextSetRGBFillColor(ctxt, 0, 0, 0, 1);
                CGContextFillRect(ctxt, CGRectMake(0.0, 0.0, thumbsize.width, thumbsize.height));
                CGContextSetRGBFillColor(ctxt, 1, 1, 1, 1);
            }
            
            else {
                CGContextSetRGBFillColor(ctxt, 1, 1, 1, 1);
                CGContextFillRect(ctxt, CGRectMake(0.0, 0.0, thumbsize.width, thumbsize.height));
                CGContextSetRGBFillColor(ctxt, 0, 0, 0, 1);
            }
            
            int counter = 0;
            unsigned long limit = 5;
            
            if ([brusheslist count] <= 6) {
                limit = [brusheslist count] - 1;
            }
            
            while (counter <= limit) {
                
                NSString * brushfolder = brusheslist[counter];
                NSString *brushpath = [brushfolder stringByAppendingString:@"/QuickLook/Thumbnail.png"];
                
                NSTask *unzipTask2 = [NSTask new];
                [unzipTask2 setLaunchPath:@"/usr/bin/unzip"];
                [unzipTask2 setStandardOutput:[NSPipe pipe]];
                [unzipTask2 setArguments:@[@"-p", [URL path], brushpath]];
                [unzipTask2 launch];
                
                NSData *brushdata = [[[unzipTask2 standardOutput] fileHandleForReading] readDataToEndOfFile];
                
                NSBitmapImageRep * image = [NSBitmapImageRep imageRepWithData:brushdata];
                
                CGImageRef imageref = image.CGImage;
                
                CGSize size = CGSizeMake(image.size.width/2, image.size.height/2);
                size = CGSizeMake(420, 200);
                
                int position_x = (counter % 2) * 420;
                int position_y = 400;
                if (counter > 1 && counter <= 3) {
                    position_y = 200;
                }
                if (counter > 3) {
                    position_y = 0;
                }
                
                CGRect smallthumbrect = CGRectMake(position_x, position_y, size.width, size.height);
                
                CGContextClipToMask(ctxt, smallthumbrect, imageref);
                CGContextFillRect(ctxt, smallthumbrect);
                CGContextResetClip(ctxt);
                
                counter += 1;
            }
            
            QLPreviewRequestFlushContext(preview, ctxt);
            CGContextRelease(ctxt);
        }
        
        if ([file_extension isEqual: @"swatches"]) {
            NSTask *unzipTask = [NSTask new];
            [unzipTask setLaunchPath:@"/usr/bin/unzip"];
            [unzipTask setStandardOutput:[NSPipe pipe]];
            [unzipTask setArguments:@[@"-p", [URL path], @"Swatches.json"]];
            [unzipTask launch];
            
            NSData *thumbdata = nil;
            
            thumbdata = [[[unzipTask standardOutput] fileHandleForReading] readDataToEndOfFile];
            
            NSError *jsonError;
            
            NSMutableArray *swatches_array = [[NSMutableArray alloc] init];
            swatches_array = [NSJSONSerialization JSONObjectWithData:thumbdata options:NSJSONReadingMutableLeaves error:&jsonError];
            if(jsonError) {
                // check the error description
                NSLog(@"json error : %@", [jsonError localizedDescription]);
            } else {
                // use the jsonDictionaryOrArray
                NSDictionary *swatch_dict = swatches_array[0];
                NSMutableArray *colors_list = [swatch_dict objectForKey:@"swatches"];
                
                CGSize swatch_thumb_size = CGSizeMake(418, 124);
                CGSize swatch_size = CGSizeMake(40, 40);
                CGContextRef ctxt = QLPreviewRequestCreateContext(preview, swatch_thumb_size, true, nil);
                CGContextAddRect(ctxt, CGRectMake(0,0,swatch_size.width,swatch_size.height));
                
                CGContextSetRGBFillColor(ctxt, 0.1, 0.1, 0.1, 1);
                
                CGContextFillRect(ctxt, (CGRect){CGPointZero, swatch_thumb_size});
                
                int index = 0;
                while (index < 30) {
                    // Create NSColor from HSB values
                    NSDictionary *color;
                    if (index < [colors_list count]) {
                        color = colors_list[index];
                    }
                    if (![color isEqual:[NSNull null]]) {
                        CGFloat hue = [[color objectForKey:@"hue"] floatValue];
                        CGFloat saturation = [[color objectForKey:@"saturation"] floatValue];
                        CGFloat brightness = [[color objectForKey:@"brightness"] floatValue];
                        NSColor *swatch_color = [NSColor colorWithHue:hue saturation:saturation brightness:brightness alpha:1.0];
                        CGContextSetRGBFillColor(ctxt, [swatch_color redComponent], [swatch_color greenComponent], [swatch_color blueComponent], 1.0);
                        
                        CGPoint position = getSwatchPreviewPosition(index);
                        CGContextFillRect(ctxt, (CGRect){position, swatch_size});
                    } else {
                        CGContextSetRGBFillColor(ctxt, 0.05, 0.05, 0.05, 1);
                        CGPoint position = getSwatchPreviewPosition(index);
                        CGContextFillRect(ctxt, (CGRect){position, swatch_size});
                    }
                    index++;
                }
                
                QLPreviewRequestFlushContext(preview, ctxt);
                CGContextRelease(ctxt);
            }
        }
        
    }

    return noErr;
}

void CancelPreviewGeneration(void *thisInterface, QLPreviewRequestRef preview)
{
    // Implement only if supported
}
