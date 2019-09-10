import pygame
import binascii
import random
import os
import winsound

# CHIP 8 EMULATOR:
# http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/
# http://devernay.free.fr/hacks/chip8/C8TECH10.HTM
# https://en.wikipedia.org/wiki/CHIP-8#Opcode_table
# TODO: FX29 Opcode (font sprites). Fix Collision detection.

class Chip8:
    opcodeSize = 2
    memorySize = 4096
    stackSize = 16

    opcode = 0x000
    memory = []
    V = []
    I = 0x000
    pc = 0x200

    # [64 x 32]
    gfx = []

    delay_timer = 0
    sound_timer = 0
    soundBuzzer = False
    drawFlag = False

    stack = []
    sp = 0

    key = []
    
    pixelSurface = pygame.Surface((640,320))

    def processCycle(self):
    
        # Fetch Opcode
        self.opcode = self.memory[self.pc] << 8| self.memory[self.pc + 1]
        # (left-shift 8 bits then 
        # Bitwise OR between current PC location and next PC location)
        # (because an Opcode is 2 bytes long)

        # Decipher Opcode        
        opcodeFirstByte = self.opcode >> 8 & 0xFF
        opcodeSecondByte = self.opcode & 0xFF
        
        opcodeFirstNibble = opcodeFirstByte >> 4 & 0xF
        opcodeSecondNibble = opcodeFirstByte & 0x0F
        opcodeThirdNibble = self.opcode >> 4 & 0xF
        opcodeFourthNibble = self.opcode & 0xF
        opcodeLastTwoNibbles = self.opcode & 0xFF
        opcodeLastThreeNibbles = self.opcode & 0xFFF
       
        # Execute Opcode (following Opcode table ordering)
        # (Then move PC to next opcode unless we're directly calling memory)
       
        #0NNN - Call - not implemented
        
        #00E0 - Display - clears the screen
        if(self.opcode == 0x00E0): 
            drawFlag = False
            self.gfx = bytearray(64 * 32)
            self.pc += 2
        
        #00EE - Return - returns from a subroutine
        if(self.opcode == 0x00EE):
            self.pc = self.stack[len(self.stack) - 1]
            self.stack.pop()
            self.pc += 2
            
        #1NNN - jump to memory address at NNN
        if(opcodeFirstNibble == 0x1):
            self.pc = opcodeLastThreeNibbles
        
        #2NNN - calls subroutine at NNN
        if(opcodeFirstNibble == 0x2):
            self.stack.append(self.pc)
            self.pc = opcodeLastThreeNibbles
            
        #3XNN - Skips the next instruction if VX equals NN
        if(opcodeFirstNibble == 0x3):
            if self.V[opcodeSecondNibble] == opcodeSecondByte:
                self.pc += 4
            else: self.pc += 2
            
        #4XNN - Skips the next instruction if VX does NOT equal NN
        if(opcodeFirstNibble == 0x4):
            if not self.V[opcodeSecondNibble] == opcodeSecondByte:
                self.pc += 4
            else: self.pc += 2
            
            
        #5XY0 Skips the next instruction if VX equals VY
        if(opcodeFirstNibble == 0x5):
            if self.V[opcodeSecondNibble] == self.V[opcodeThirdNibble]:
                self.pc += 4
            else: self.pc += 2
            
        #6XNN Sets VX to NN
        if(opcodeFirstNibble == 0x6):
            self.V[opcodeSecondNibble] = opcodeSecondByte
            self.pc += 2   
            
        #7XNN Adds NN to VX
        if(opcodeFirstNibble == 0x7):
            if(self.V[opcodeSecondNibble] + opcodeSecondByte > 255): self.V[opcodeSecondNibble] = (self.V[opcodeSecondNibble] + opcodeSecondByte) - 255
            else: self.V[opcodeSecondNibble] += opcodeSecondByte
            self.pc += 2
            
        # A few different 0x8XYN bitwise operations...
        if(opcodeFirstNibble == 0x8):
            #8XY0 Sets VX to the value of VY
            if(opcodeFourthNibble == 0x0):
                self.V[opcodeSecondNibble] = self.V[opcodeThirdNibble]
                self.pc += 2
            #8XY1 Sets VX to VX OR (Bitwise OR) VY
            if(opcodeFourthNibble == 0x1):
                self.V[opcodeSecondNibble] |= self.V[opcodeThirdNibble]
                self.pc += 2
            #8XY2 sets VX to VX AND (Bitwise AND) VY     
            if(opcodeFourthNibble == 0x2):
                self.V[opcodeSecondNibble]  &= self.V[opcodeThirdNibble]
                self.pc += 2
            #8XY3 Sets VX to VX XOR XY
            if(opcodeFourthNibble == 0x3):
                self.V[opcodeSecondNibble] ^= self.V[opcodeThirdNibble] 
            #8XY4 Adds VY to VX (and sets VF to 1 if there's a carry)
            if(opcodeFourthNibble == 0x4):    
                if(self.V[opcodeSecondNibble] + self.V[opcodeThirdNibble] > 255):
                    self.V[0xF] = 1
                    self.V[opcodeSecondNibble] += (self.V[opcodeThirdNibble] - 255)
                else: 
                    self.V[0xF] = 0
                    self.V[opcodeSecondNibble] += self.V[opcodeThirdNibble]
                self.pc += 2
            #8XY5 VY is subtracted from VX. (VF is 1 if there's a borrow)
            if(opcodeFourthNibble == 0x5):
                if(self.V[opcodeSecondNibble] - self.V[opcodeThirdNibble] < 0):
                    self.V[0xF] = 1
                    self.V[opcodeSecondNibble] = (self.V[opcodeSecondNibble] - self.V[opcodeThirdNibble]) + 255
                else:
                   self.V[0xF] = 0
                   self.V[opcodeSecondNibble] -= self.V[opcodeThirdNibble]
                self.pc += 2
            #8XY6 Stores least significant bit of VX in VF then shifts VX to the right by 1
            if(opcodeFourthNibble == 0x6):    
                self.V[0xF] = self.V[opcodeSecondNibble] & 0xF
                self.V[opcodeSecondNibble] >> 1
                self.pc += 2
            #8XY7 Sets VX to VY minus VX (sets VF to 0 if there's a borrow)    
            if(opcodeFourthNibble == 0x7):
                if(self.V[opcodeThirdNibble] - self.V[opcodeSecondNibble] < 0):
                    self.V[0xF] = 0
                    self.V[opcodeSecondNibble] = self.V[opcodeThirdNibble] - self.V[opcodeSecondNibble] + 255
                else:
                    self.V[0xF] = 1
                    self.V[opcodeSecondNibble] = self.V[opcodeThirdNibble] - self.V[opcodeSecondNibble]
                pc += 2    
            #8XYE Stores most significant bit of VX in VF and shifts VX left by 1
            if(opcodeFourthNibble == 0xE):    
                self.V[0xF] = self.V[opcodeSecondNibble] >> 2 & 0xF
                self.V[opcodeSecondNibble] << 1
                self.pc += 2
                
        #9XY0 Skips next instruction if VX doesn't equal VY        
        if(opcodeFirstNibble == 0x9):
            if(not self.V[opcodeSecondNibble] == self.V[opcodeThirdNibble]):
                self.pc += 4
            else: self.pc += 2
            
        #ANNN Sets I to the address NNN
        if(opcodeFirstNibble == 0xA):
            self.I = opcodeLastThreeNibbles
            self.pc += 2
            
        #BNNN Jumps to address NNN plus V0
        if(opcodeFirstNibble == 0xB):
            pc = opcodeLastThreeNibbles + self.V[0]
            
        #CXNN Sets VX to result of (random number between 0 and 25) AND NN
        if(opcodeFirstNibble == 0xC):
            self.V[opcodeSecondNibble] = random.randint(0,255) & opcodeLastTwoNibbles
            self.pc += 2
        
        # DXYN Draws a sprite at coordinate (VX, VY)
        # Each pixel has width 8, height N
        # Each row of 8 pixels is read starting from location I
        # VF is set to 1 if any pixels are flipped from 1 to 0
        if(opcodeFirstNibble == 0xD):
            self.drawFlag = True
            self.V[0xF] = 0
            # Get our X,Y,N values
            startX = self.V[opcodeSecondNibble]
            startY = self.V[opcodeThirdNibble]
            numberOfEightPixelRows = opcodeFourthNibble
            
            #XOR these values against what's already in gfx
            pixelIterator = startX + (startY * 64)  # Will keep track of all pixels
            rowIterator = 0 # Will keep track of 8 pixels per row
            columnIterator = 0 # Will keep track of current column
            
            while(columnIterator < numberOfEightPixelRows):
                
                pixel = self.memory[self.I + columnIterator]
                rowIterator = 0
                
                while(rowIterator < 8):
                    
                    if pixel & (0x80 >> rowIterator) != 0:
                        
                        if startX + rowIterator > 63: startX = 0
                        if startY + columnIterator > 31: startY = 0
                    
                        oldGFX = self.gfx[(startX + rowIterator + ((startY + columnIterator) * 64))]
                        
                        self.gfx[(startX + rowIterator + ((startY + columnIterator) * 64))] ^= 1
                        
                        newGFX = self.gfx[(startX + rowIterator + ((startY + columnIterator) * 64))]
                        
                        if(oldGFX == 1 and newGFX == 0): 
                            self.V[0xF] = 1
                            VFSet = True
                    rowIterator += 1
                columnIterator += 1
            self.pc += 2
        
        
        if(opcodeFirstNibble == 0xE):
            # EX9E Skips next instruction if key stored in VX is pressed
            if(opcodeLastTwoNibbles == 0x9E):
                if(self.key[self.V[opcodeSecondNibble]] != 0):
                    self.pc += 4
                else: self.pc += 2
                        
            
            # EXA1 Skips next instruction if key stored in VX is NOT pressed
            if(opcodeLastTwoNibbles == 0xA1):
                if(self.key[self.V[opcodeSecondNibble]] != 0):
                    self.pc += 2
                else: self.pc += 4       
        
        # A few 0xF operations to finish the opcode table...
        if(opcodeFirstNibble == 0xF):
            
            # FX07 Sets delay to the value of the delay timer
            if(opcodeLastTwoNibbles == 0x07):
                self.V[opcodeSecondNibble] = self.delay_timer
                self.pc += 2
            
            # FX0A A key pressed is awaited, and then stored in VX
            # (ALL INSTRUCTION HALTED UNTIL NEXT KEY EVENT)
            if(opcodeLastTwoNibbles == 0x0A):
                
                keyPressed = False
                keyPressedValue = 0
                while(not keyPressed):
                   keyIterator = 0
                   if self.keys[keyIterator] != 0: 
                       keyPressedValue = keyIterator
                       break
                   keyIterator += 1
                   if(keyIterator >= 16): keyIterator = 0
            
                
                self.V[opcodeSecondNibble] = keyPressedValue
                self.pc += 2
        
            #FX15 Sets the delay timer to VX
            if(opcodeLastTwoNibbles == 0x15):
                self.delay_timer = self.V[opcodeSecondNibble]
                self.pc += 2
                
            #FX18 Sets the sound timer to VX
            if(opcodeLastTwoNibbles == 0x18):
                self.sound_timer = self.V[opcodeSecondNibble]
                self.pc += 2
                
            # TODO: FX29 Sets I to the location of the sprite for
            # the character in VX. Characters 0-F hex are represented
            # by a 4x6 font
            if(opcodeLastTwoNibbles == 0x29):
                self.pc += 2
            
            # FX33 Stores the binary-coded decimal of VX.
            # Most Significant Digit [of 3] stored at I, Middle digit
            # at I+1, Least Significant at I+2
            if(opcodeLastTwoNibbles == 0x33):
                self.memory[self.I] = (int)((self.V[opcodeSecondNibble] / 100) % 10)
                self.memory[self.I + 1] = (int)((self.V[opcodeSecondNibble] / 10) % 10)
                self.memory[self.I + 2] = (int)((self.V[opcodeSecondNibble]) % 10)
                self.pc += 2
                
            # FX55 Stores V0 to VX (inc VX) in memory starting at I.
            # I remains unmodified
            if(opcodeLastTwoNibbles == 0x55):
                storageIterator = 0
                while storageIterator < opcodeSecondNibble:
                    self.memory[self.I + storageIterator] = self.V[storageIterator]
                    storageIterator += 1
                self.pc += 2
                
            # FX65 Fills V0 to VX (inc VX) with values from memory starting at I
            # I remains unmodified
            if(opcodeLastTwoNibbles == 0x65):
                storageIterator = 0
                while storageIterator < opcodeSecondNibble:
                    self.V[storageIterator] = self.memory[self.I + storageIterator]
                    storageIterator += 1
                self.pc += 2
        
        #Update timers
        if(not self.delay_timer <= 0): self.delay_timer -= 1
        if(not self.sound_timer <= 0): self.sound_timer -= 1
        
        return

    def loadGame(self, filename):
        with open(filename, "rb") as binary_file:
           data = binary_file.read()
           os.system('cls')
           print("Raw ROM dump:")
           print(data.hex())
           fileLengthInBytes = os.path.getsize(filename)
           print("File size: " + (str)(fileLengthInBytes) + " bytes")
           
           # Fill memory beginning at location 512 with ROM instructions
           memoryCounter = 0x200
           fileIterator = 0
           while(fileIterator < fileLengthInBytes):
               binary_file.seek(fileIterator)
               self.memory[memoryCounter] = data[fileIterator]
               fileIterator += 1
               memoryCounter += 1
            
        return

    def drawGraphics(self):
        
        self.pixelSurface = pygame.Surface((640, 320))
        
        # Iterate through the graphics array of 1s and 0s
        # If 1, draw a white pixel
        # If 0, draw nothing 
        
        rowLength = 64
        numberOfColumns = 32
        startX = 0
        startY = 0 
        pixelIterator = 0
        rowIterator = 0
        columnIterator = 0

        while(pixelIterator < 2048):
            if(self.gfx[pixelIterator] == 1):
                pygame.draw.rect(self.pixelSurface, (255,255,255), ((startX + rowIterator) * 10,(startY + columnIterator) * 10,10,10), 0)
                
            pixelIterator += 1
            rowIterator += 1
            
            if rowIterator >= rowLength:
                rowIterator = 0
                columnIterator += 1
            if startX > rowLength - 1: startX = 0
            if startY > numberOfColumns - 1: startY = 0
        return

    def setKeys(self):
        return

def main():
    pygame.init()
    
    chip8 = Chip8()
    
    # Initialize memory
    chip8.memory = bytearray(chip8.memorySize)
    
    # Initialize registers
    chip8.V = bytearray(16)
    
    # Initialize the pixels
    chip8.gfx = bytearray(2048)
        
    # Clear the stack
    chip8.stack = []
    chip8.sp = 0

    # Initialize key state array
    chip8.key = bytearray(16)
    
    # Initialize timers
    chip8.delay_timer = 0
    chip8.sound_timer = 0
    
    # Initialize sound
    frequency = 2500
    duration = 1000
        
    chip8.loadGame("pong.rom")
        
    running = True
    gameClock = pygame.time.Clock()
    screen = pygame.display.set_mode((840,480))
    pygame.display.set_caption("CHIP-8 Python Emulator")
    
    debugFont = pygame.font.SysFont("arial", 20)
        
    while(running):  
                
        # Write out Program Counter
        pcTitleSurface = debugFont.render("Program counter location", True, (255,255,255))
        pcSurface = debugFont.render((str)(chip8.pc), True, (255,255,255))
        screen.blit(pcSurface, (30, 380))
        screen.blit(pcTitleSurface, (30, 360))
        
        # Write out index register
        ITitleSurface = debugFont.render("Index register location", True, (255,255,255))
        ISurface = debugFont.render((str)(chip8.I), True, (255,255,255))
        screen.blit(ISurface, (150, 340))
        screen.blit(ITitleSurface, (110, 320))
        
        # -------------------Main emulation loop ------------------------- #

        if(chip8.drawFlag): 
            chip8.drawGraphics()
            screen.blit(chip8.pixelSurface, (0,0))
            
        chip8.processCycle()
        
        # ---------------------------------------------------------------- #   
           
        # UI rendering
        pygame.draw.line(screen, (255,255,255), (640,0), (640,480), 2)
        pygame.draw.line(screen, (255,255,255), (0,320), (640, 320), 2)
        
        # Write out Opcode
        opcodeTitleSurface = debugFont.render("Opcode", True, (255,255,255))
        opcodeSurface = debugFont.render(hex(chip8.opcode), True, (255,255,255))
        screen.blit(opcodeSurface, (30, 340))
        screen.blit(opcodeTitleSurface, (30, 320))
        
        # Write out register contents
        vTitleSurface = debugFont.render("Register contents", True, (255,255,255))
        screen.blit(vTitleSurface, (240, 410))
        startX = 10
        for byte in chip8.V:
            vSurface = debugFont.render((str)(byte), True, (255,255,255))
            screen.blit(vSurface, (startX, 440))
            startX += 40
                  
        for event in pygame.event.get():
            if(event.type == pygame.KEYDOWN):
                if event.key == pygame.K_ESCAPE:
                    running = False 
                # Hex keyboard (8,4,6,2 directional input per numpad)
                if event.key == pygame.K_w:
                    chip8.key[1] = 0xFF
                if event.key == pygame.K_s:
                    chip8.key[4] = 0xFF
                    
                if event.key == pygame.K_UP:
                    chip8.key[0xC] = 0xFF
                if event.key == pygame.K_DOWN:
                    chip8.key[0xD] = 0xFF
            
            if(event.type == pygame.KEYUP):
                 if event.key == pygame.K_w:
                     chip8.key[1] = 0x0
                 if event.key == pygame.K_s:
                     chip8.key[4]  = 0x0 
                 
                 if event.key == pygame.K_UP:
                        chip8.key[0xC] = 0x0
                 if event.key == pygame.K_DOWN:
                    chip8.key[0xD] = 0x0 
                                              
        # Audio plays on non-zero sound timer
        if(chip8.sound_timer != 0): print('\a')
        
        pygame.display.update() 
        screen.fill((0,0,0))
        gameClock.tick(300)

main()