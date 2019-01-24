"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Parts of this code were originally based on the gtp module 
in the Deep-Go project by Isaac Henrion and Amos Storkey 
at the University of Edinburgh.
"""
import re
import traceback
from sys import stdin, stdout, stderr
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
    MAXSIZE, coord_to_point, is_black_white
import numpy as np

class GtpConnection():

    def __init__(self, go_engine, board, debug_mode = False):
        self.blackMax = None
        self.whiteMax = None
        self.dictStoreWhiteMove = None
        self.dictStoreBlackMove = None
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board: 
            Represents the current board state.
        """
        self._debug_mode = debug_mode
        self.go_engine = go_engine
        self.board = board
        self.thisboard = self.board.board
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd
        }

        # used for argument checking
        # values: (required number of arguments, 
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}')
        }

    def write(self, data):
        stdout.write(data) 

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection. 
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".
                               format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write('? {}\n\n'.format(error_msg))
        stdout.flush()

    def respond(self, response=''):
        """ Send response to stdout """
        stdout.write('= {}\n\n'.format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))
        
    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the  Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.dictStoreWhiteMove = {}
        self.dictStoreBlackMove = {}
        self.colorMax = {'b': 0,'w': 0}
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    """
    ==========================================================================
    Assignment 1 - game-specific commands start here
    ==========================================================================
    """

    def gogui_analyze_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )

    def gogui_rules_game_id_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond("Gomoku")

    def gogui_rules_board_size_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        self.respond(str(self.board.size))

    def gogui_rules_legal_moves_cmd(self, args):
        """ Implement this function for Assignment 1 """
        # TODO SHOULD BE DONE
        # -------------------------
        # you need to deal with some cases,
        # case 1: when the board is full, no legal moves should return
        # case 2: when one side is win, no legal moves should return
        # case 3: return all possible legal moves, if either cases NOT happened
        # refer to the Go program
        if self.colorMax['w'] >= 5 or self.colorMax['b'] >= 5:
            self.respond()
        else:
            moves = self.board.get_empty_points()
            gtp_moves = []
            for move in moves:
                coords = point_to_coord(move, self.board.size)
                gtp_moves.append(format_point(coords))
                # print(format_point(coords))
            sorted_moves = ' '.join(sorted(gtp_moves))
            self.respond(sorted_moves.upper())

    def gogui_rules_side_to_move_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args):
        """ We already implemented this function for Assignment 1 """
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                #str += '.'
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)
            
    def gogui_rules_final_result_cmd(self, args):
        '''gogui-rules_final_result'''
        """ Implement this function for Assignment 1 """
        '''return black or white wins or no winners'''
        result = "unknown"
        if len(self.board.get_empty_points()) == 0:
            self.respond("draw")
            '''evaluation goes after draw! '''
        else:
            if self.colorMax['w'] >= 5:
                self.respond("white win")
            elif self.colorMax['b'] >= 5:
                self.respond("black win")
            else:
                self.respond(result)

    # def simple_play_move(self, point, color):
    #     assert is_black_white(color)
    #     if self.thisboard[point] != EMPTY:
    #         return False
    #     self.thisboard[point] = color
    #     self.current_player = GoBoardUtil.opponent(color)
    #     return True

    def play_cmd(self, args):
        """ Modify this function for Assignment 1 """
        """
        play a move args[1] for given color args[0] in {'b','w'}
        """
        #print(args) # ['B/W', "position"]
        try:
            board_color = args[0].lower()
            board_move = args[1]
            color = color_to_int(board_color)
            if args[1].lower() == 'pass':
                self.board.play_move(PASS, color)
                self.board.current_player = GoBoardUtil.opponent(color)
                self.respond()
                return
            coord = move_to_coord(args[1], self.board.size)
            if coord:
                move = coord_to_point(coord[0],coord[1], self.board.size)
            else:
                self.error("Error executing move {} converted from {}"
                           .format(move, args[1]))
                return  #do not exist coord!!!

            # one more evaluation, if one side wins, then play should not continue!!!
            if self.colorMax['w'] >= 5 or self.colorMax['b'] >= 5:
                self.respond("One side is win game over!")
                return
            # Once executed uptill here, it means , all above conditions passed,
            # and we should check if that space is empty or not
            # if yes, then place the chess on that space, otherwise not!
            if not self.board.play_move(move, color):
                self.respond("Illegal Move: {}".format(board_move))
                return  # repeated play in that coord!!!
            else:
                #has been successfully executed 'self.board.play_move'
                self.debug_msg("Move: {}\nBoard:\n{}\n".
                                format(board_move, self.board2d()))
                # insert the information into dictionary
                self.insertKeyIntoDict(args[0],coord,move)
            self.respond()
        except Exception as e:
            self.respond('Error: {}'.format(str(e)))

    def genmove_cmd(self, args):
        """ TODO """
        """ generate a move for color args[0] in {'b','w'} """
        # ------------------------
        # this function needs some simple modification, such that
        # if one side is win, it will not generate any position to move, but return '[resign]'
        if self.colorMax['w'] >= 5 or self.colorMax['b'] >= 5:
            self.respond("resign")
        else:
            board_color = args[0].lower()
            color = color_to_int(board_color)
            move = self.go_engine.get_move(self.board, color)
            move_coord = point_to_coord(move, self.board.size)
            move_as_string = format_point(move_coord)
            if self.board.is_legal(move, color):
                self.board.play_move(move, color)
                self.respond(move_as_string)
            else:
                self.respond("Illegal move: {}".format(move_as_string))

    def insertKeyIntoDict(self,color,coord,move):
        dictPointer = {}
        if color.lower() == "w":

            dictPointer = self.dictStoreWhiteMove
        elif color.lower() =="b":

            dictPointer = self.dictStoreBlackMove
        dictPointer.setdefault(coord,{'upDown':1,'leftRight':1,'backslash':1,"forwardslash":1})
        for key,value in dictPointer.get(coord).items():
            if key == 'upDown':
                upNighbour = (coord[0]-1,coord[1])
                downNighbour = (coord[0]+1,coord[1])
                #print(upNighbour,downNighbour)
                if upNighbour in dictPointer.keys():

                    dictPointer.get(coord)['upDown'] += dictPointer.get(upNighbour)['upDown']   #update the current step
                    #dictPointer.get(upNighbour)['upDown'] = dictPointer.get(coord)['upDown']   #update last step
                    # use while loop to update all past steps
                    counter = 1
                    while upNighbour in dictPointer.keys():
                        dictPointer.get(upNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                        upNighbour = (coord[0]-1-counter,coord[1])
                        counter +=1
                if downNighbour in dictPointer.keys():

                    dictPointer.get(coord)['upDown'] += dictPointer.get(downNighbour)['upDown']
                    #dictPointer.get(downNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                    counter = 1
                    while downNighbour in dictPointer.keys():
                        dictPointer.get(downNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                        downNighbour = (coord[0]+1+counter,coord[1])
                        counter +=1
                #re-update upnighbor again!
                upNighbour = (coord[0] - 1, coord[1])
                counter = 1
                while upNighbour in dictPointer.keys():
                    dictPointer.get(upNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                    upNighbour = (coord[0] - 1 - counter, coord[1])
                    counter += 1
            if key == 'leftRight':
                leftNighbour = (coord[0], coord[1] - 1)
                rightNighbour = (coord[0], coord[1] + 1)
                if leftNighbour in dictPointer.keys():
                    dictPointer.get(coord)['leftRight'] += dictPointer.get(leftNighbour)['leftRight']
                    counter = 1
                    while leftNighbour in dictPointer.keys():
                        dictPointer.get(leftNighbour)['leftRight'] = dictPointer.get(coord)['leftRight']
                        leftNighbour = (coord[0], coord[1] - 1 - counter)
                        counter += 1
                if rightNighbour in dictPointer.keys():

                    dictPointer.get(coord)['leftRight'] += dictPointer.get(rightNighbour)['leftRight']
                    #dictPointer.get(downNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                    counter = 1
                    while rightNighbour in dictPointer.keys():
                        dictPointer.get(rightNighbour)['leftRight'] = dictPointer.get(coord)['leftRight']
                        rightNighbour = (coord[0],coord[1] +1+counter)
                        counter +=1
                # re-update upnighbor again!
                leftNighbour = (coord[0], coord[1] - 1)
                counter = 1
                while leftNighbour in dictPointer.keys():
                    dictPointer.get(leftNighbour)['leftRight'] = dictPointer.get(coord)['leftRight']
                    leftNighbour = (coord[0], coord[1]- 1 - counter)
                    counter += 1
            if key =="forwardslash":
                leftDownNighbour = (coord[0]-1, coord[1] +1)
                rightUpNighbour = (coord[0]+1, coord[1]-1)
                if leftDownNighbour in dictPointer.keys():

                    dictPointer.get(coord)['forwardslash'] += dictPointer.get(leftDownNighbour)['forwardslash']   #update the current step
                    #dictPointer.get(upNighbour)['upDown'] = dictPointer.get(coord)['upDown']   #update last step
                    # use while loop to update all past steps
                    counter = 1
                    while leftDownNighbour in dictPointer.keys():
                        dictPointer.get(leftDownNighbour)['forwardslash'] = dictPointer.get(coord)['forwardslash']
                        leftDownNighbour = (coord[0]-1-counter,coord[1] + 1 + counter)
                        counter +=1
                if rightUpNighbour in dictPointer.keys():

                    dictPointer.get(coord)['forwardslash'] += dictPointer.get(rightUpNighbour)['forwardslash']
                    #dictPointer.get(downNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                    counter = 1
                    while rightUpNighbour in dictPointer.keys():
                        dictPointer.get(rightUpNighbour)['forwardslash'] = dictPointer.get(coord)['forwardslash']
                        rightUpNighbour = (coord[0]+1+counter,coord[1]-1-counter)
                        counter +=1
                # re-update upnighbor again!
                leftDownNighbour = (coord[0]-1, coord[1] +1)
                counter = 1
                while leftDownNighbour in dictPointer.keys():
                    dictPointer.get(leftDownNighbour)['forwardslash'] = dictPointer.get(coord)['forwardslash']
                    leftDownNighbour = (coord[0] - 1 - counter, coord[1]+1 + counter)
                    counter += 1
            if key == 'backslash':
                leftUpNighbour = (coord[0] - 1, coord[1] - 1)
                rightDownNighbour = (coord[0] + 1, coord[1] + 1)
                if leftUpNighbour in dictPointer.keys():

                    dictPointer.get(coord)['backslash'] += dictPointer.get(leftUpNighbour)['backslash']   #update the current step
                    #dictPointer.get(upNighbour)['upDown'] = dictPointer.get(coord)['upDown']   #update last step
                    # use while loop to update all past steps
                    counter = 1
                    while leftUpNighbour in dictPointer.keys():
                        dictPointer.get(leftUpNighbour)['backslash'] = dictPointer.get(coord)['backslash']
                        leftUpNighbour = (coord[0]-1-counter,coord[1] - 1 - counter)
                        counter +=1
                if rightDownNighbour in dictPointer.keys():

                    dictPointer.get(coord)['backslash'] += dictPointer.get(rightDownNighbour)['backslash']
                    #dictPointer.get(downNighbour)['upDown'] = dictPointer.get(coord)['upDown']
                    counter = 1
                    while rightDownNighbour in dictPointer.keys():
                        dictPointer.get(rightDownNighbour)['backslash'] = dictPointer.get(coord)['backslash']
                        rightDownNighbour = (coord[0]+1+counter,coord[1]+1+counter)
                        counter +=1
                # re-update upnighbor again!
                leftUpNighbour = (coord[0] - 1, coord[1] - 1)
                counter = 1
                while leftUpNighbour in dictPointer.keys():
                    dictPointer.get(leftUpNighbour)['backslash'] = dictPointer.get(coord)['backslash']
                    leftUpNighbour = (coord[0] - 1 - counter, coord[1] - 1 - counter)
                    counter += 1
            #print(key,value)

        # -------------------------------------------------
        # Update the corrosponding max value for that color
        # Tell the program, if one side is win!!!
        # -------------------------------------------------
        #print(self.colorMax.get(color.lower()))
        for key, value in dictPointer.get(coord).items():
            if value > self.colorMax.get(color.lower()):
                 self.colorMax[color.lower()] = value
        #print("max pointer is " + str(self.colorMax.get(color.lower())))


    """
    ==========================================================================
    Assignment 1 - game-specific commands end here
    ==========================================================================
    """

    def showboard_cmd(self, args):
        self.respond('\n' + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    """ Assignment 1: ignore this command, implement 
        gogui_rules_legal_moves_cmd  above instead """
    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move,self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)


def point_to_coord(point, boardsize):
    """
    Transform point given as board array index 
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)

def format_point(move):
    """
    Return move coordinates as a string such as 'a1', or 'pass'.
    """
    column_letters = "abcdefghjklmnopqrstuvwxyz"
    if move == PASS:
        return "pass"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1]+ str(row) 
    
def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("invalid point: '{}'".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("point off board: '{}'".format(s))
    return row, col

def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK , "w": WHITE, "e": EMPTY, 
                    "BORDER": BORDER}
    return color_to_int[c] 
