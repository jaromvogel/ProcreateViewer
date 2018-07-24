
import struct

from SiModel import SiDocument
from BaseWriter import BaseWriter

#
# Used to export an SiDocument into a PSD file.
#
# Specification can be found here:
#
#   http://www.adobe.com/devnet-apps/photoshop/fileformatashtml/
#
# Example:
#
#   # Load a Procreate document
#   document = SiDocument( fileName )
#
#   # Write it out to a PSD file
#   writer = PsdWriter( document )
#   writer.write( "~/Desktop/outFile.psd" )
#
class PsdWriter( BaseWriter ):

    def __init__( self, document ):
    
        super.__init__( document )
            
    
    def write( self, fileName ):
    
        super.write( fileName )
        
        # Open file, set everything up
        self.openFile()
        
        # Do the actual output
        self.writePsd()
        
    
    def writePsd( self ):
    
        self.writeHeader()
        self.writeColorModeData()
        self.writeImageResources()
        self.writeLayerAndMaskInfo()
        self.writeCompositeData()

        
    def writeHeader( self ):
        
        # Signature
        self.file.write( b"8BPS" )
        
        # Version
        self.putUInt16( 1 )
        
        # 6 bytes reserved, set to 0
        self.file.write( b"\x0\x0\x0\x0\x0\x0" )
        
        # Number of channels (R G B A in our case)
        # Or are these spare channels for the Channels panel?
        # In that case we should use 0 instead
        self.putUInt16( 4 )
        
        # Image size (indeed height first, then width)
        self.putUInt32( self.document.height )
        self.putUInt32( self.document.width )
        
        # Bits per channel (8-bit for now)
        self.putUInt16( 8 )
        
        # Color mode (RGB in our case)
        self.UInt16( 3 )
        
    
    def writeColorModeData( self ):
        
        # Color mode data is 0 bytes in length (we don't write any since we're RGB)
        self.putUInt32( 0 )
        
    
    def writeImageResources( self ):
        
        # Length of the image resources section (we currently don't write anything)
        self.putUInt32( 0 )
        
    
    def writeLayerAndMaskInfo( self ):
        
        # We go back to this offset later when we know how much data we have
        # actually written
        layerAndMaskInfoSectionLenFieldOffset = self.file.tell()
        
        # Length of the layer and mask info section.
        # Put 0 for now and come back to here after we are done writing the
        # section
        self.putUInt32( 0 )
        
        # The layer and mask info section consists of a layer info
        # section and a mask info section.
        self.writeLayerInfoSection()
        self.writeMaskInfoSection()
        
        # TODO: Additional layer information section goes here
        
        # Now we need to go back and write the size of the section, which we put
        # off until now
        currPos = self.file.tell()
        # Figure out how many bytes we have written since then and subtract
        # the size of the actual length field
        sectionLen = currPos - layerAndMaskInfoSectionLenFieldOffset - 4
        self.file.seek( layerAndMaskInfoSectionLenFieldOffset )
        self.putUInt32( sectionLen )
        # Now go back to the output position we were at
        self.file.seek( currPos )
        
        
    # This is the first part of the Layer and Mask Info section
    def writeLayerInfoSection( self ):
        
        # We store the offset of this field since we defer writing it until
        # later
        layerInfoSectionLengthFieldOffset = self.file.tell()
        
        # Length of the layer info section, rounded to next multiple of 2.
        # Instead of pre-calculating this, we write it after we have actually
        # written the section
        self.putUInt32( 0 )
    
        # Number of layers in the document
        self.putInt16( len( self.document.layers ) ) )
    
        # Write info about each layer into the file
        for layer in self.document.layers:
            self.writeLayerInfo( layer )

        # Write the image data for each layer into the file
        for layer in self.document.layers:
            self.writeChannelImageData( layer )

        # Now that we are done, calculate how much data we have written and
        # update that pesky length field before this section
        currPos = self.file.tell()
        sectionLen = currPos - layerInfoSectionLengthFieldOffset - 4
        
        # If this section's length is not a multiple of 2, we need to pad it
        if sectionLen % 2 != 0:
            sectionLen += 1
            self.putUInt8( 0 )
        
        self.file.seek( layerInfoSectionLengthFieldOffset )
        self.putUInt32( sectionLen )
        
        # We use relative seek here since we did the tell() before writing
        # the padding and adjusting the sectionLen. currPos would not include
        # the padding byte.
        self.file.seek( sectionLen, 1 )


    # This is the second part of the Layer and Mask section
    def writeMaskInfoSection( self ):
        
        # Not sure which of the tables in this bloody spec document this
        # actually is supposed to be, but if it's the
        # "Layer mask / adjustment layer data" table, then this should work
        
        # Length field - we don't write any data
        putUInt32( 0 )
        
    
    # This is Layer and Mask Info Section -> Layer Info Section -> This for each layer
    def writeLayerInfo( self, layer ):
        
        # Layer bounds rectangle. Spec says 4*4 bytes, but not if signed or not.
        self.putUInt32( layer.rect.top.x )
        self.putUInt32( layer.rect.top.y )
        self.putUInt32( layer.rect.bottom.x )
        self.putUInt32( layer.rect.bottom.y )
    
        # Number of channels in the layer (we have RGBA)
        self.putUInt16( 4 )
        
        # Compute the data length for an individual channel.
        # Since we don't use compression, this is pretty straightforward
        bytesPerChannel = 1 # only support 8-bit for now
        channelLength = self.document.width * self.document.height * bytesPerChannel
        
        # Channel info for Red
        self.putInt16( 0 ) # 0 = red
        self.putUInt32( channelLength )
        
        # Channel info for Green
        self.putInt16( 1 ) # 1 = green
        self.putUInt32( channelLength )
        
        # Channel info for Blue
        self.putInt16( 2 ) # 2 = blue
        self.putUInt32( channelLength )
        
        # Channel info for Alpha
        self.putInt16( -1 ) # -1 = transparency
        self.putUInt32( channelLength )
        
        # Blend mode signature
        self.file.write( b"8BIM" )

        # Blend mode key
        self.file.write( blendModeToPs( layer.blendModeToString( layer.blendMode ) ) )
    
        # Layer opacity
        self.putUInt8( layer.opacity * 255 )

        # Clipping (0 = base, 1 = non-base, whatever that means)
        self.putUInt8( 1 )

        # Flags. Only relevant one is bit #1 (counting from zero), which
        # indicates visibility. Not 100% sure from which side we are counting,
        # but the second bit in my mind would mean 2^6 = 64. Let's see if the
        # layer shows up visible :)
        self.putUInt8( 64 )

        # One filler byte
        self.file.write( b"\x0" )

        # Length of the extra data fields. We write that after we are done
        # writing it, so we save the offset and put zero for now
        extraDataSizeFieldOffset = self.file.tell()
        self.putUInt32( 0 )
        
        # ----- extra data fields section starts here -----

        # Layer mask data size. We don't write any, so we write zero here
        self.putUInt32( 0 )

        # Layer's blending ranges data size. We don't write any, so we write zero here
        self.putUInt32( 0 )
    
        # Layer name must be padded to multiple of 4 bytes. We have unicode
        # chars, i.e. 2 bytes per character.
        # Length field is number of unicode chars, NOT number of bytes
        numPadBytes = 4 - ( ( len( layer.name ) * 2 ) % 4 )

        self.putUInt32( len( layer.name ) )
        
        # Write layer name as unicode
        nameAsUnicode = layer.name.encode( 'utf16-le' )
        self.file.write( nameAsUnicode )
        
        # Seek back two bytes since we don't need the null terminator
        self.file.seek( -2, 1 )
        
        # Put in the padding bytes if necessary
        self.putPadding( numPadBytes )
    
        # Still got to write the length of the "extra data fields"
        currPos = self.file.tell()
        self.file.seek( extraDataSizeFieldOffset )
        self.putUInt32( currPos - extraDataSizeFieldOffset - 4 ) # -4 to exclude the size field itself
        self.file.seek( currPos )


    # Writes the actual image data for a specific layer into the file
    def writeChannelImageData( self, layer ):
        
        # 0 = raw data, 1 would be RLE
        self.putUInt16( 0 )
    
        # now follows the data. if I read the document correctly, row width
        # will be padded to an even number of bytes but not height.
        # Also, data appears to be writte per-channel, not interleaved.
        # TODO: Implement
        
        # Width needs to be padded to multiple of two and padding needs to be
        # written for each scanline
        widthPadded = self.document.width
        if widthPadded % 2 == 1:
            widthPadded += 1
        
        # Write all black data for all channels now
        self.putPadding( widthPadded * self.document.height * 4 )


    def writeCompositeData( self ):

        # If self.document.composite is set, we could actually use that to write
        # composite data here, but frankly, I'm not too keen on writing more
        # PSD-related stuff.
        pass


    # Given a plain-text blend mode string, this returns the appropriate
    # Photoshop fourcc.
    # UPDATE: Since it turns out we have an enum, not a sting,
    # this could probably be optimized somewhat...
    def blendModeToPs( self, blendMode ):
        
        # This could probably be cleaned up with a dictionary
        if blendMode == "Pass Through":
            return b"pass"
        else if blendMode == "Normal":
            return b"norm"
        else if blendMode == "Dissolve":
            return b"diss"
        else if blendMode == "Darken" or blendMode == "Minimum" or blendMode == "Min":
            return b"dark"
        else if blendMode == "Multiply":
            return b"mul "
        else if blendMode == "Color Burn":
            return b"idiv"
        else if blendMode == "Linear Burn":
            return b"lbrn"
        else if blendMode == "Darker Color":
            return b"dkCl"
        else if blendMode == "Lighten" or blendMode == "Maximum" or blendMode == "Max":
            return b"lite"
        else if blendMode == "Screen":
            return b"scrn"
        else if blendMode == "Color Dodge":
            return b"div "
        else if blendMode == "Linear Dodge" or blendMode == "Add":
            return b"lddg"
        else if blendMode == "Lighter Color":
            return b"lgCl"
        else if blendMode == "Overlay":
            return b"over"
        else if blendMode == "Soft Light":
            return b"sLit"
        else if blendMode == "Hard Light":
            return b"hLit"
        else if blendMode == "Vivid Light":
            return b"vLit"
        else if blendMode == "Linear Light":
            return b"lLit"
        else if blendMode == "Pin Light":
            return b"pLit"
        else if blendMode == "Hard Mix":
            return b"hMix"
        else if blendMode == "Difference":
            return b"diff"
        else if blendMode == "Exclusion":
            return b"smud"
        else if blendMode == "Subtract":
            return b"fsub"
        else if blendMode == "Divide":
            return b"fdiv"
        else if blendMode == "Hue":
            return b"hue "
        else if blendMode == "Saturation":
            return b"sat "
        else if blendMode == "Color":
            return b"colr"
        else if blendMode == "Luminosity":
            return b"lum "
        else
            # For anything else, we default to "Normal"
            return b"norm"


    # ...