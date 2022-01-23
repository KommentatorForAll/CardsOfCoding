import sys
import re
from typing import List, Dict

arguments = sys.argv

num_multipliers = {
    'c': 0,
    'h': 1,
    's': 2,
    'd': 3
}


def validate_card(card: str):
    return re.match('[dcsh]\\d{1,2}', card) and int(card[1:]) in range(1, 14)


def parse_card(pos: int, program: List[str]):
    card = program[pos]
    if not validate_card(card):
        raise SyntaxError(f'Invalid card at instruction {pos + 1}, {card}')

    shade = card[0]
    number = int(card[1:])
    return shade, number


def find_code_block(pos, program):
    j = pos
    in_expr = False
    next_expr = False
    depth = 1
    while j < len(program):
        if program[j] in ['d3', 'd4', 'd5']:
            depth += 1
        if program[j] in ['d5', 'd6', 'h5' 'h6'] and not in_expr:
            next_expr = True
            j += 1
        if not next_expr:
            if program[j] == 'd2' and not in_expr:
                depth -= 1
                if depth == 0:
                    return program[pos:j]
            if program[j] == 'c3':
                in_expr = not in_expr
        next_expr = False
        j += 1
    raise EOFError(f'unable to find end of codeblock of block {pos} in section {program}')


def parse_number_expression(pos: int, program: List[str], stack: List[int], heap: Dict[str, int]):
    num = 0
    pos_incr = 1

    shade, number = parse_card(pos, program)

    if shade == 'c':
        if number == 1:
            return ord(input()), 1
        elif number == 2:
            return int(input()), 1
        elif number == 3:
            cur_shade, cur_num = parse_card(pos + pos_incr, program)
            while cur_shade != 'c' or cur_num != 3:
                pos_incr += 1
                num += num_multipliers[cur_shade] * cur_num
                cur_shade, cur_num = parse_card(pos + pos_incr, program)
            return num, pos_incr + 1

    elif shade == 'h':
        if number == 2:
            if len(stack) == 0:
                raise IndexError('tried to pop from an empty stack')
            return stack.pop(), 1
        elif number == 5:
            key = program[pos + pos_incr]
            return heap.get(key, 0), pos_incr + 1

    elif shade == 's':
        if number in range(1, 6):
            num_1, first_pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            num_2, second_pos_incr = parse_number_expression(pos + first_pos_incr + 1, program, stack, heap)
            pos_incr += first_pos_incr + second_pos_incr
            if number == 1:
                return num_1 + num_2, pos_incr
            elif number == 2:
                return num_1 - num_2, pos_incr
            elif number == 3:
                return num_1 * num_2, pos_incr
            elif number == 4:
                return num_1 // num_2, pos_incr
            elif number == 5:
                return num_1 % num_2, pos_incr
        elif number == 6:
            num_1, first_pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            pos_incr += first_pos_incr
            return num_1 == 0, pos_incr
    raise SyntaxError(f'invalid number expression at position {pos}, {program[pos]}')


def execute_single(pos: int, program: List[str], stack: List[int], heap: Dict[str, int],
                   codeblocks: Dict[str, List[str]]):
    shade, number = parse_card(pos, program)

    if shade == 'c':
        if number == 4:
            num, pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            print(chr(num), end='')
            return pos_incr + 1
        elif number == 5:
            num, pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            print(num, end='')
            return pos_incr + 1

    elif shade == 'h':
        if number == 1:
            num, pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            stack.append(num)
            return pos_incr + 1
        elif number == 3:
            stack.append(stack.pop(-2))
            return 1
        elif number == 4:
            heap[program[pos + 1]], pos_incr = parse_number_expression(pos + 2, program, stack, heap)
            return pos_incr + 2
        elif number == 6:
            stack.append(stack[-1])
            return 1

    elif shade == 'd':
        if number == 3:
            num, pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            code = find_code_block(pos + pos_incr + 2, program)
            if num != 0:
                execute(code, stack, heap, codeblocks)
            return pos_incr + 3 + len(code)
        elif number == 4:
            num, pos_incr = parse_number_expression(pos + 1, program, stack, heap)
            code = find_code_block(pos + pos_incr + 2, program)
            while num != 0:
                execute(code, stack, heap, codeblocks)
                num, _ = parse_number_expression(pos + 1, program, stack, heap)
            return pos_incr + 3 + len(code)
        elif number == 5:
            block = find_code_block(pos + 3, program)
            codeblocks[program[pos + 1]] = block
            return len(block) + 4
        elif number == 6:
            code = codeblocks[program[pos + 1]]
            execute(code, stack, heap, codeblocks)
            return 2
    raise SyntaxError(f'invalid instruction at position {pos}, {program[pos]}')


def execute(program: List[str], stack=None, heap=None, codeblocks=None):
    if stack is None:
        stack = []
    if heap is None:
        heap = dict()
    if codeblocks is None:
        codeblocks = dict()

    i = 0
    amount_instr = len(program)
    while i < amount_instr:
        i += execute_single(i, program, stack, heap, codeblocks)


if __name__ == '__main__':
    if len(arguments) == 0 or arguments[0] == 'help':
        print('trying to help you')
    else:
        with open(arguments[1]) as f:
            execute(f.read().split())
