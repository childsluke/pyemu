import pygame
import binascii
import os

# CHIP 8 EMULATOR:
# http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/
# So far reached 'Start the emulation' (using pong.rom)

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

    def processCycle(self):
    
        # Fetch Opcode
        self.opcode = self.memory[self.pc] << 8| self.memory[self.pc + 1]
        # (left-shift 8 bits then 
        # Bitwise OR between current PC location and next PC location)
    
        # Execute Opcode (following Opcode table ordering)
    
        if(self.opcode == 0x00E0): drawFlag = False
        if(self.opcode == 0xd000): drawFlag = True
    
        # Update timers
        self.pc += 2 
        if(self.pc > 4095): self.pc = 0
        
        # Put this opcode on the stack
        if len(self.stack) == self.stackSize:
            self.stack.pop()
        self.stack.append(self.opcode)
        
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
        # Iterate through the graphics array of 1s and 0s
        # If 1, draw a white pixel
        # If 0, draw nothing  
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
    gfx = bytearray(2048)
        
    # Clear the stack
    chip8.stack = []
    chip8.sp = 0

    # Initialize key state array
    chip8.key = bytearray(16)
        
    chip8.loadGame("pong.rom")
        
    running = True
    gameClock = pygame.time.Clock()
    screen = pygame.display.set_mode((840,480))
    
    debugFont = pygame.font.SysFont("arial", 20)
        
    # Emulation loop
    while(running):  
        
        # UI rendering
        pygame.draw.line(screen, (255,255,255), (640,0), (640,480), 2)
        pygame.draw.line(screen, (255,255,255), (0,320), (640, 320), 2)
        
        # Opcode
        opcodeTitleSurface = debugFont.render("Current Opcode", True, (255,255,255))
        opcodeSurface = debugFont.render(hex(chip8.opcode), True, (255,255,255))
        screen.blit(opcodeSurface, (30, 340))
        screen.blit(opcodeTitleSurface, (30, 320))
        
        # Program Counter
        pcTitleSurface = debugFont.render("Current PC place", True, (255,255,255))
        pcSurface = debugFont.render((str)(chip8.pc), True, (255,255,255))
        screen.blit(pcSurface, (30, 380))
        screen.blit(pcTitleSurface, (30, 360))
        
        chip8.processCycle()
        
        if(chip8.drawFlag): chip8.drawGraphics()
        
        chip8.setKeys()
        
        gameClock.tick(60)
        
        for event in pygame.event.get():
            if(event.type == pygame.KEYDOWN):
                if event.key == pygame.K_ESCAPE:
                    running = False
                  
        pygame.display.flip() 
        screen.fill((0,0,0))

main()