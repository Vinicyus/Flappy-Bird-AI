import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 680

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (300,40)
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")
programIcon = pygame.image.load(os.path.join("imgs", "bird_icon.png"))
pygame.display.set_icon(programIcon)

clock = pygame.time.Clock()
GAME_FPS = 30
MENU_FPS = 5

GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

extrasmallfont = pygame.font.SysFont("comicsansms", 15)
smallfont = pygame.font.SysFont("comicsansms", 25)
medfont = pygame.font.SysFont("comicsansms", 50)
largefont = pygame.font.SysFont("comicsansms", 65)

white = (255, 255, 255)
black = (0, 0, 0)
colorD1 = (121, 212, 241)
colorL1 = (207, 241, 232)
colorD2 = (240, 223, 115)
colorL2 = (229, 239, 197)
colorD3 = (115, 240, 144)
colorL3 = (207, 243, 215)


#### Objects ####
class Bird:
	IMGS = BIRD_IMGS
	MAX_ROTATION = 25
	ROT_VEL = 20
	ANIMATION_TIME = 5

	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.tilt = 0
		self.tick_count = 0
		self.vel = 0
		self.height = self.y
		self.img_count = 0
		self.img = self.IMGS[0]

	def jump(self):
		self.vel = -10.5
		self.tick_count = 0
		self.height = self.y

	def move(self):
		self.tick_count +=1

		d = self.vel * self.tick_count + 1.5 * self.tick_count **2

		if d >= 16:
			d = 16

		if d < 0:
			d -= 2

		self.y = self.y + d

		if d < 0 or self.y < self.height + 50:
			if self.tilt < self.MAX_ROTATION:
				self.tilt = self.MAX_ROTATION
		else:
			if self.tilt > -90:
				self.tilt -= self.ROT_VEL

	def draw(self, win):
		self.img_count += 1

		if self.img_count < self.ANIMATION_TIME:
			self.img = self.IMGS[0]
		elif self.img_count < self.ANIMATION_TIME*2:
			self.img = self.IMGS[1]
		elif self.img_count < self.ANIMATION_TIME*3:
			self.img = self.IMGS[2]
		elif self.img_count < self.ANIMATION_TIME*4:
			self.img = self.IMGS[1]
		elif self.img_count == self.ANIMATION_TIME*4 + 1:
			self.img = self.IMGS[0]
			self.img_count = 0

		if self.tilt <= -80:
			self.img = self.IMGS[1]
			self.img_count = self.ANIMATION_TIME*2

		rotated_image = pygame.transform.rotate(self.img, self.tilt)
		new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
		win.blit(rotated_image, new_rect.topleft)

	def get_mask(self):
		return pygame.mask.from_surface(self.img)

class Pipe:
	GAP = 200
	VEL = 5

	def __init__(self, x):
		self.x = x
		self.height = 0
		self.gap = 100

		self.top = 0
		self.bottom = 0
		self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
		self.PIPE_BOTTOM = PIPE_IMG

		self.passed = False
		self.set_height()

	def set_height(self):
		self.height = random.randrange(50, 350)
		self.top = self.height - self.PIPE_TOP.get_height()
		self.bottom = self.height + self.GAP

	def move(self):
		self.x -= self.VEL

	def draw(self, win):
		win.blit(self.PIPE_TOP, (self.x, self.top))
		win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

	def collide(self, bird):
		bird_mask = bird.get_mask()
		top_mask = pygame.mask.from_surface(self.PIPE_TOP)
		bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

		top_offset = (self.x - bird.x, self.top - round(bird.y))
		bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

		b_point = bird_mask.overlap(bottom_mask, bottom_offset)
		t_point = bird_mask.overlap(top_mask, top_offset)

		if t_point or b_point:
			return True

		return False

class Base:
	VEL = 5
	WIDTH = BASE_IMG.get_width()
	IMG = BASE_IMG

	def __init__(self, y):
		self.y = y
		self.x1 = 0
		self.x2 = self.WIDTH

	def move(self):
		self.x1 -= self.VEL
		self.x2 -= self.VEL

		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 + self.WIDTH

		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 + self.WIDTH

	def draw(self, win):
		win.blit(self.IMG, (self.x1, self.y))
		win.blit(self.IMG, (self.x2, self.y))


#### AI ####
def draw_window_AI(birds, pipes, base, score, gen):
	win.blit(BG_IMG, (0,0))

	for pipe in pipes:
		pipe.draw(win)

	text = medfont.render("Score: " + str(score), 1,white)
	win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 15))

	text = medfont.render("Gen: " + str(gen), 1,white)
	win.blit(text, (10, 15))

	text = extrasmallfont.render("Press R to return to the main menu.", 1,white)
	win.blit(text, (10, 5))

	base.draw(win)

	for bird in birds:
		bird.draw(win)
	pygame.display.update()

def eval_genomes(genomes, config):
	global GEN
	GEN += 1
	nets = []
	ge = []
	birds = []

	for _, g in genomes:
		net = neat.nn.FeedForwardNetwork.create(g, config)
		nets.append(net)
		birds.append(Bird(230,350))
		g.fitness = 0
		ge.append(g)


	base = Base(610)
	pipes = [Pipe(600)]

	score = 0

	run = True
	while run:
		clock.tick(GAME_FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_r:
					game_intro()

		pipe_ind = 0
		if len(birds) > 0:
			if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
				pipe_ind = 1
		else:
			run = False
			break

		for x, bird in enumerate(birds):
			bird.move()
			ge[x].fitness += 0.1

			output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

			if output[0] > 0.5:
				bird.jump()

		add_pipe = False
		rem = []
		for pipe in pipes:
			for x, bird in enumerate(birds):	
				if pipe.collide(bird):
					ge[x].fitness -= 1
					birds.pop(x)
					nets.pop(x)
					ge.pop(x)

				if not pipe.passed and pipe.x < bird.x:
					pipe.passed = True
					add_pipe = True

			if pipe.x + pipe.PIPE_TOP.get_width() < 0:
				rem.append(pipe)

			pipe.move()

		if add_pipe:
			score  += 1
			for g in ge:
				g.fitness += 5
			pipes.append(Pipe(600))

		for r in rem:
			pipes.remove(r)

		for x, bird in enumerate(birds):		
			if bird.y + bird.img.get_height() >= 610 or bird.y < 0:
				birds.pop(x)
				nets.pop(x)
				ge.pop(x)

		base.move()
		draw_window_AI(birds, pipes, base, score, GEN)


def run(config_file):
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
						neat.DefaultSpeciesSet, neat.DefaultStagnation, config_file)

	p = neat.Population(config)

	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats)

	winner = p.run(eval_genomes,50)

def AI():
	if __name__ == "__main__":
		local_dir = os.path.dirname(__file__)
		config_path = os.path.join(local_dir, "config-feedforward.txt")
		run(config_path)

#### Normal Game ####
def main():
	bird = Bird(200,250)
	base = Base(610)
	pipes = [Pipe(600)]
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	# clock = pygame.time.Clock()

	score = 0
	start = False
	while start == False:
		clock.tick(GAME_FPS)
		draw_window(bird, pipes, base, score, True)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					start = True
					bird.jump()

	run = True
	while run:
		clock.tick(GAME_FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					bird.jump()

		bird.move()
		add_pipe = False
		rem = []
		for pipe in pipes:
			if pipe.collide(bird):
				gameOver = True
				display_message(score)

			if pipe.x + pipe.PIPE_TOP.get_width() < 0:
				rem.append(pipe)

			if not pipe.passed and pipe.x < bird.x:
				pipe.passed = True
				add_pipe = True

			pipe.move()

		if add_pipe:
			score  += 1
			pipes.append(Pipe(600))

		for r in rem:
			pipes.remove(r)

		if bird.y + bird.img.get_height() >= 610:
			display_message(score)

		base.move()
		draw_window(bird, pipes, base, score)

	pygame.quit()
	quit()

def draw_window(bird, pipes, base, score, start_message = False):
	win.blit(BG_IMG, (0,0))

	for pipe in pipes:
		pipe.draw(win)

	text = medfont.render("Score: " + str(score), 1,white)
	win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

	if start_message:
		message = extrasmallfont.render("Press SPACE to start the game.", 1, white)
		win.blit(message, ((WIN_WIDTH/2) - (message.get_width()/2), 150))

	base.draw(win)

	bird.draw(win)
	pygame.display.update()

def display_message(score):
	if score > 0:
		f = open('scores.txt', 'a')
		f.writelines(str(score) + "\n")
		f.close()
	pygame.time.delay(1000)
	win.blit(BG_IMG, (0,0))
	gameOver = True
	while gameOver:
		text = medfont.render("Game over!", 1, white)
		txt_score = smallfont.render("Your score: " + str(score), 1, white)
		press_Q = smallfont.render("Press Q to quit.", 1, white)
		press_P = smallfont.render("Press P to play it again.", 1, white)
		press_R = smallfont.render("Press R to return to the main menu.", 1, white)
		win.blit(text, (WIN_WIDTH/2 - text.get_width()/2, (WIN_HEIGHT/2 - text.get_height()/2) - 200))
		win.blit(txt_score, (WIN_WIDTH/2 - txt_score.get_width()/2, (WIN_HEIGHT/2 - txt_score.get_height()/2) - 100))
		win.blit(press_Q, (WIN_WIDTH/2 - press_Q.get_width()/2, (WIN_HEIGHT/2 - press_Q.get_height()/2) -50))
		win.blit(press_P, (WIN_WIDTH/2 - press_P.get_width()/2, (WIN_HEIGHT/2 - press_P.get_height()/2)))
		win.blit(press_R, (WIN_WIDTH/2 - press_R.get_width()/2, (WIN_HEIGHT/2 - press_R.get_height()/2) + 50))
		pygame.display.update()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					pygame.quit()
				if event.key == pygame.K_p:
					main()
				if event.key == pygame.K_r:
					game_intro()
		clock.tick(MENU_FPS)

def text_objects(text, color, size):
	if size == "extrasmall":
		textSurface = extrasmallfont.render(text, True, color)
	elif size == "small":
		textSurface = smallfont.render(text, True, color)
	elif size == "medium":
		textSurface = medfont.render(text, True, color)
	elif size == "large":
		textSurface = largefont.render(text, True, color)

	return textSurface, textSurface.get_rect()

def text_to_button(msg, color, buttonx, buttony, buttonwidth, butonheight, size="small"):
	textSurf, textRect = text_objects(msg, color, size)
	textRect.center = ((buttonx+(buttonwidth/2), buttony+(butonheight/2)))
	win.blit(textSurf, textRect)

def button(text, x, y, width, height, inactive_color, active_color, action = None):
	cur = pygame.mouse.get_pos()
	click = pygame.mouse.get_pressed()
	if x + width > cur[0] > x and y + height > cur[1] > y:
		pygame.draw.rect(win, active_color, (x, y, width, height))
		if click[0] == 1 and action != None:
			if action == "quit":
				pygame.quit()
				quit()
			if action == "record":
				records()
			if action == "play":
				main()
			if action == "ai":
				AI()
	else:
		pygame.draw.rect(win, inactive_color, (x, y, width, height))

	text_to_button(text, white, x, y, width, height)

def message_to_screen(msg,color, y_displace=0, size = "small"):
	textSurf, textRect = text_objects(msg, color, size)
	textRect.center = (WIN_WIDTH/2), (WIN_HEIGHT/2) + y_displace
	win.blit(textSurf, textRect)

def records():
	record = True
	file = open('scores.txt')
	lines = sorted(file.readlines(), reverse = True, key = int)
	while record:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_r:
					game_intro()
				elif event.key == pygame.K_q:
					pygame.quit()
					quit()

		win.blit(BG_IMG, (0,0))
		message_to_screen("Records", white, -210, "large")
		message_to_screen("Top 10 Scores", white, -160, "extrasmall")

		lineHeight = -130
		i = 0
		for line in lines:
			line = line[:-1]
			message_to_screen(str(i + 1) + "°: " + str(line), white, lineHeight, "small")
			lineHeight += 30
			i += 1
			if i == 10:
				break
		file.close()

		message_to_screen("Press R to return to the main menu", white, 210, "extrasmall")

		pygame.display.update()
		clock.tick(MENU_FPS)

def game_intro():
	intro = True
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	while intro:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_q:
					pygame.quit()
					quit()

		win.blit(BG_IMG, (0,0))
		message_to_screen("Flappy Bird", white, -150, "large")
		message_to_screen("You can play the game or watch an AI playing.", white, -90, "extrasmall")

		button("Play", 200,300,100,50, colorD1, colorL1, action="play" )
		button("Your Records", 163,375,175,50, colorD2, colorL2, action="record")
		button("Watch AI playing", 125,450,250,50, colorD3, colorL3, action="ai")

		pygame.display.update()
		clock.tick(MENU_FPS)

game_intro()
