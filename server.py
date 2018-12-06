"""Tag Multiplayer Game Server

This game will take place on a simple game board in which each 
"""

import socket
import threading
import sys
import random

W, H = (10, 10)
PORT = 3210
PACKET_SIZE = 128
board = [['.' for x in range(W)] for y in range(H)]

valid_pieces = 'WM@#$%&X'

valid_commands = ['JOIN', 'INFO', 
                  'MOVE_UP', 'MOVE_DOWN', 'MOVE_LEFT', 'MOVE_RIGHT',
                  'TAG_UP', 'TAG_DOWN', 'TAG_LEFT', 'TAG_RIGHT',
                  'QUIT']

class GameHandler(object):
	"""The GameHandler will mostly be used as a singleton to keep track of everything and run the game."""
	# TODO: Thread that runs and updates the game.

	def __init__(self):
		self.new_game(False)

	def new_game(self, keep_players=True):
		if keep_players:

			# Move each player to a random position, make one of them it
			positions = []
			for player in self.players:
				self.set_it(False)
				while True:
					new_pos = (random.randint(0, W), random.randint(0, H))
					if new_pos not in positions:
						player.set_position(new_pos)
						positions.append(new_pos)
						break

			chosen_player = random.choice(self.players)
			chosen_player.set_it(True)
			self.it_player = chosen_player

		else:
			self.players = {}
			self.used_pieces = []
			self.it_player = None

	def add_player(self, addr, piece):
		if piece in self.used_pieces:
			return False
		p = Player
		p.piece = piece
		self.players[addr] = p
		self.used_pieces.append(piece)
		return True

	def move_player(self, addr, direction):
		moving_player = self.players[addr]
		new_x, new_y = moving_player.position
		if direction == 'UP':
			new_y -= 1
		elif direction == 'DOWN':
			new_y += 1
		elif direction == 'LEFT':
			new_x -= 1
		elif direction == 'RIGHT':
			new_x += 1

		new_position = (clamp(new_x, 0, W), clamp(new_y, 0, H))
		for player in self.players:
			if player.position == new_position:
				return "ERROR, PLAYER ALREADY THERE"
		self.players[addr].set_position(new_position)
		return "SUCCESS"

	def tag_player(self, addr, direction):
		moving_player = self.players[addr]
		if not moving_player.it:
			return "ERROR, NOT IT"
		tag_x, tag_y = moving_player.position
		if direction == 'UP':
			new_y -= 1
		elif direction == 'DOWN':
			new_y += 1
		elif direction == 'LEFT':
			new_x -= 1
		elif direction == 'RIGHT':
			new_x += 1

		tag_position = (clamp(new_x, 0, W), clamp(new_y, 0, H))
		
		for player in self.players:
			if player.position == tag_position:
				moving_player.set_it(False)
				player.set_it(True)
				self.it_player = player
				break
		return "SUCCESS"

	def get_unused_pieces(self):
		return "".join(piece for piece in valid_pieces if piece not in self.used_pieces)

	def run_game(self):
		pass

	def kick_player(self, addr):
		if addr in self.players:
			del self.players[addr]
			return True
		return False
		
class Player(object):

	def __init__(self):
		self.it = False
		self.position = (0, 0)
		self.piece = None

	def set_position(self, position):
		self.position = position

	def set_it(self, it):
		self.it = it

GLOBAL_GAME_HANDLER = GameHandler()

def send_game_state():
	data = []
	for player in players:
		data.append(player)

def send_game_help():
	data = "size=({},{})".format(W, H) + ",commands=(" + ",".join(valid_commands) + ")"
	return data

def parse_msg(msg, conn):
	"""On recieving a message from a connection, this method parses it and returns what the response should be"""
	try:
		addr = "{}:{}".format(*conn.getpeername())
		print(addr)

		vals = tuple(map(lambda m: m.strip(), msg.split(':')))
		print(vals)
		if len(vals) != 2:
			return "INVALID MESSAGE. PLEASE USE THE FORMAT 'COMMAND : ARGUMENTS'"
		command, args = vals
		command = command.upper()
		if command == 'QUIT':
			GLOBAL_GAME_HANDLER.kick_player(addr)
			return '<QUIT>' # Special value
		if command == 'INFO':
			return send_game_help()
		elif command == 'JOIN':
			if GLOBAL_GAME_HANDLER.add_player(addr, args):
				return "JOIN REQUEST ACCEPTED, YOUR TOKEN IS [{}], WAITING FOR PLAYERS".format(args)
			else:
				return "ERROR, PIECE ALREADY TAKEN. UNUSED PIECES: " + GLOBAL_GAME_HANDLER.get_unused_pieces()
		elif command.startswith('MOVE') and command in valid_commands:
			return GLOBAL_GAME_HANDLER.move_player(addr, command[5:])
		elif command.startswith('TAG') and command in valid_commands:
			return GLOBAL_GAME_HANDLER.tag_player(addr, command[5:])
		else:
			return "INVALID MESSAGE. PLEASE USE THE FORMAT 'COMMAND : ARGUMENTS'"
	except Exception as err:
		raise(err)
		return "SERVER ERROR, PLEASE TRY AGAIN AT A LATER TIME"

def display_board():
	"""Print the board out in a human-friendly view"""
	print("-" * (2 * W + 1))
	for row in board:
		print("|" + " ".join(row) + "|")
	print("-" * (2 * W + 1))

def handle_client(conn):
	"""The function that gets run by a thread each time a new user connects."""
	with conn:
		done = False

		while not done:
			msg = b''
			while True:
				data = conn.recv(PACKET_SIZE)
				msg += data
				if len(msg) < PACKET_SIZE:
					break

			response = parse_msg(msg.decode(), conn).encode()
			if response == b'<QUIT>':
				done = True
				conn.sendall(b'GOODBYE')
			else:
				conn.sendall(response)

def run_game():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(('localhost', PORT))
	# s.setblocking(False)
	s.listen(len(valid_pieces))

	game_threads = []
	it_player = None

	print("Listening on:", PORT)
	while True:
		try:
			conn, addr = s.accept()
			print(conn, addr)
			print(addr, 'connected.')
			gt = threading.Thread(None, handle_client, 'Thread-'+str(len(game_threads)), (conn,))
			game_threads.append(gt)
			gt.start()
		except socket.timeout as err:
			print(err)
			continue
		except BlockingIOError as err:
			continue
		except KeyboardInterrupt:
			sys.exit()

def clamp(val, high, low):
	return min(max(val, low), high)

if __name__ == "__main__":
	run_game()