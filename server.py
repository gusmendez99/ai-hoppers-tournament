import socket
import sys
import random
import numpy as np
import time
import utils
from settings import *
# Game
from hoppers.game.board import Board
from hoppers.game.referee import Referee

WINNER = False
TIME_EXP = False

if len(sys.argv) <= 1:
    print("usage: server.py <port>")
    sys.exit()

board = Board()
board.init_pieces()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

    server_port = int(sys.argv[1])
    server_address = (SERVER_DEFAULT_IP, server_port)

    sock.bind(server_address)
    sock.listen(5)

    connections = []

    while len(board.players) < MAX_PLAYERS and len(connections) < MAX_PLAYERS:
        print("Waiting for players ... ")
        conn, addr = sock.accept()
        print("One player entered!")
        board.players.append(addr)
        connections.append(conn)

    print("Game ready!")
    referee = Referee()
    board.pp_board()

    # Turn will be choose as follow:
    #   The first one to be connected will have TURN 1 and placed at (0,0) [Red]
    #   The second one to be connected will have TURN 2, and placed at (9,9) [Blue]

    connections[0].send(f"{REGISTER}(0,0)".encode())
    connections[1].send(f"{REGISTER}(9,9)".encode())

    start = time.time()

    while not WINNER or not TIME_EXP:
        # TODO: make refactor, the two players do the same...
        # Start to receive moves
        print("Waiting for new move from Player 1...")
        first_player_req = connections[0].recv(BUFF_SIZE)
        
        # Parse bytes response to string
        first_player_req = first_player_req.decode()
        action, payload = first_player_req[0], first_player_req[1:]
        
        # Validate player 1 & action
        if action == NEW_MOVE:
            dict_move = utils.from_xml(payload)

            initial_row, initial_col = int(dict_move['from']['@row']), int(dict_move['from']['@col'])
            final_row, final_col = int(dict_move['to']['@row']), int(dict_move['to']['@col'])

            # Finally, we need to move the piece placed at initial position
            new_move = [
                (initial_row, initial_col), 
                (final_row, final_col)
            ]

            print(f"Move received: {initial_row},{initial_col} to {final_row},{final_col}")
            legal_moves = referee.generate_legal_moves(new_move[0][0], new_move[0][1], board.get_board())
            print("Legal moves:", legal_moves)
            referee.clear_prev_spots()
            # TODO: modify move_piece() and return a bool if movement was performed successfully

            if new_move[1] in legal_moves:
                board.move_piece(new_move[0], new_move[1])
                # Send move to the opponent
                connections[1].send(f"{NEW_MOVE}{payload}".encode())
            else:
                print("Illegal move")
                # Send error to the opponent
                connections[1].send(f"{ILLEGAL_MOVE}".encode())

            board.pp_board()
            winner = board.detect_win()
            if winner[0]:
                print("Player 1 wins")
                WINNER = True

            if winner[1]:
                print ("Player 2 wins")
                WINNER = True
            
            board.change_turn()

        
        print("Waiting for new move from Player 2...")
        second_player_req = connections[1].recv(BUFF_SIZE)
        
        # Parse bytes response to string
        second_player_req = second_player_req.decode()
        action, payload = second_player_req[0], second_player_req[1:]
        
        # Validate player 2 & action
        if action == NEW_MOVE:
            dict_move = utils.from_xml(payload)

            initial_row, initial_col = int(dict_move['from']['@row']), int(dict_move['from']['@col'])
            final_row, final_col = int(dict_move['to']['@row']), int(dict_move['to']['@col'])

            # Finally, we need to move the piece placed at initial position
            new_move = [
                (initial_row, initial_col), 
                (final_row, final_col)
            ]


            print(f"Move received: {initial_row},{initial_col} to {final_row},{final_col}")
            legal_moves = referee.generate_legal_moves(new_move[0][0], new_move[0][1], board.get_board())
            print("Legal moves:", legal_moves)
            referee.clear_prev_spots()
            # TODO: modify move_piece() and return a bool if movement was performed successfully
            if new_move[1] in legal_moves:
                board.move_piece(new_move[0], new_move[1])
                # Send move to the opponent
                connections[0].send(f"{NEW_MOVE}{payload}".encode())
            else:
                print("Illegal move")
                # Send error to the opponent
                connections[0].send(f"{ILLEGAL_MOVE}".encode())

            board.pp_board()
            winner = board.detect_win()
            if winner[0]:
                print("Player 1 wins")
                WINNER = True

            if winner[1]:
                print ("Player 2 wins")
                WINNER = True

            board.change_turn()

        #check time
        end = time.time()
        elapsed = end - start
        if elapsed >= TIME_LIMIT:
            TIME_EXP = True
            print("Time has expired")
    

    # Close connection
    sock.close()

    # Send game status to both players
    connections[0].send(f"{GAME_END}".encode())
    connections[1].send(f"{GAME_END}".encode())

    # If time has expired, we need to decide a winner based on best board
    print("[END] Time has expired, we need to choose a winner...")
    board.pp_board()


