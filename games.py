# games.py
import random
from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum

class GameResult(Enum):
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"

@dataclass
class GameOutcome:
    result: GameResult
    multiplier: float
    win_amount: float
    game_data: dict

class CoinFlip:
    """Игра в монетку - 50/50 шанс, выплата x1.9"""
    
    MULTIPLIER = 1.9
    
    @staticmethod
    def play(bet_amount: float, player_choice: str) -> GameOutcome:
        choices = ['heads', 'tails']
        result = random.choice(choices)
        
        if player_choice == result:
            win_amount = bet_amount * CoinFlip.MULTIPLIER
            return GameOutcome(
                result=GameResult.WIN,
                multiplier=CoinFlip.MULTIPLIER,
                win_amount=win_amount,
                game_data={'player_choice': player_choice, 'result': result}
            )
        else:
            return GameOutcome(
                result=GameResult.LOSE,
                multiplier=0,
                win_amount=0,
                game_data={'player_choice': player_choice, 'result': result}
            )

class Dice:
    """Игра в кости - угадай число от 1 до 6"""
    
    MULTIPLIER = 5.7  # ~95% RTP
    
    @staticmethod
    def play(bet_amount: float, player_guess: int) -> GameOutcome:
        if player_guess < 1 or player_guess > 6:
            raise ValueError("Number must be between 1 and 6")
        
        result = random.randint(1, 6)
        
        if player_guess == result:
            win_amount = bet_amount * Dice.MULTIPLIER
            return GameOutcome(
                result=GameResult.WIN,
                multiplier=Dice.MULTIPLIER,
                win_amount=win_amount,
                game_data={'player_guess': player_guess, 'result': result}
            )
        else:
            return GameOutcome(
                result=GameResult.LOSE,
                multiplier=0,
                win_amount=0,
                game_data={'player_guess': player_guess, 'result': result}
            )

class HighLow:
    """High/Low - угадай выше или ниже 50"""
    
    MULTIPLIER = 1.9
    
    @staticmethod
    def play(bet_amount: float, player_choice: str) -> GameOutcome:
        number = random.randint(1, 100)
        
        if number == 50:
            return GameOutcome(
                result=GameResult.DRAW,
                multiplier=1.0,
                win_amount=bet_amount,  # Возврат ставки
                game_data={'player_choice': player_choice, 'number': number}
            )
        
        is_high = number > 50
        player_wins = (player_choice == 'high' and is_high) or \
                     (player_choice == 'low' and not is_high)
        
        if player_wins:
            win_amount = bet_amount * HighLow.MULTIPLIER
            return GameOutcome(
                result=GameResult.WIN,
                multiplier=HighLow.MULTIPLIER,
                win_amount=win_amount,
                game_data={'player_choice': player_choice, 'number': number}
            )
        else:
            return GameOutcome(
                result=GameResult.LOSE,
                multiplier=0,
                win_amount=0,
                game_data={'player_choice': player_choice, 'number': number}
            )

class Slots:
    """Слоты 3x3"""
    
    SYMBOLS = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣']
    PAYOUTS = {
        '🍒': 2,
        '🍋': 3,
        '🍊': 4,
        '🍇': 5,
        '⭐': 10,
        '💎': 25,
        '7️⃣': 50
    }
    
    @staticmethod
    def spin() -> List[List[str]]:
        return [[random.choice(Slots.SYMBOLS) for _ in range(3)] for _ in range(3)]
    
    @staticmethod
    def check_wins(grid: List[List[str]]) -> List[Tuple[str, int]]:
        wins = []
        
        # Горизонтальные линии
        for row in grid:
            if row[0] == row[1] == row[2]:
                wins.append((row[0], Slots.PAYOUTS[row[0]]))
        
        # Вертикальные линии
        for col in range(3):
            if grid[0][col] == grid[1][col] == grid[2][col]:
                wins.append((grid[0][col], Slots.PAYOUTS[grid[0][col]]))
        
        # Диагонали
        if grid[0][0] == grid[1][1] == grid[2][2]:
            wins.append((grid[0][0], Slots.PAYOUTS[grid[0][0]]))
        if grid[0][2] == grid[1][1] == grid[2][0]:
            wins.append((grid[0][2], Slots.PAYOUTS[grid[0][2]]))
        
        return wins
    
    @staticmethod
    def play(bet_amount: float) -> GameOutcome:
        grid = Slots.spin()
        wins = Slots.check_wins(grid)
        
        total_multiplier = sum(w[1] for w in wins)
        win_amount = bet_amount * total_multiplier
        
        grid_display = '\n'.join([' '.join(row) for row in grid])
        
        if wins:
            return GameOutcome(
                result=GameResult.WIN,
                multiplier=total_multiplier,
                win_amount=win_amount,
                game_data={'grid': grid, 'wins': wins, 'display': grid_display}
            )
        else:
            return GameOutcome(
                result=GameResult.LOSE,
                multiplier=0,
                win_amount=0,
                game_data={'grid': grid, 'wins': [], 'display': grid_display}
            )

class Mines:
    """Мины - открывай ячейки, избегай мин"""
    
    GRID_SIZE = 5
    
    @staticmethod
    def create_game(num_mines: int = 5) -> dict:
        total_cells = Mines.GRID_SIZE * Mines.GRID_SIZE
        mine_positions = set(random.sample(range(total_cells), num_mines))
        
        return {
            'mines': list(mine_positions),
            'revealed': [],
            'num_mines': num_mines,
            'game_over': False,
            'multiplier': 1.0
        }
    
    @staticmethod
    def calculate_multiplier(revealed: int, num_mines: int) -> float:
        total = Mines.GRID_SIZE * Mines.GRID_SIZE
        safe = total - num_mines
        
        if revealed == 0:
            return 1.0
        
        multiplier = 1.0
        for i in range(revealed):
            multiplier *= (safe - i) / (total - i)
        
        return round(0.95 / multiplier, 2)  # 95% RTP
    
    @staticmethod
    def reveal_cell(game_state: dict, cell: int) -> Tuple[bool, float]:
        if cell in game_state['mines']:
            game_state['game_over'] = True
            return False, 0
        
        if cell not in game_state['revealed']:
            game_state['revealed'].append(cell)
        
        multiplier = Mines.calculate_multiplier(
            len(game_state['revealed']),
            game_state['num_mines']
        )
        game_state['multiplier'] = multiplier
        
        return True, multiplier