import pygame


width, height = 800, 600
background_color = (75, 82, 99)


screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

pygame.display.set_caption('Wizard')
screen.fill(background_color)

pygame.display.flip()

running = True
while running:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False