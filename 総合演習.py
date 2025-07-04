import tkinter as tk
import random
import os

# --- ゲームの定数 ---
WIDTH = 800
HEIGHT = 600
GROUND_Y = 450
GRAVITY = 1.2
JUMP_POWER = -20
PLAYER_X_START = 100
OBSTACLE_SPEED = -10
CLOUD_SPEED = -3
COIN_SPEED = -10
COIN_SPAWN_CHANCE = 0.6 # 障害物出現時にコインも出現する確率
MAX_COINS = 2 # 画面上のコインの最大数
HIGHSCORE_FILE = "highscores.txt"
FRAMES_PER_SECOND = 60 #一秒あたりのフレーム数

# --- グローバル変数 ---
# オブジェクトID
player = None
obstacle = None
coins = [] # 複数のコインをリストで管理
clouds = [] #雲の生成数を管理
score_text = None

# UI要素のID
start_screen_widgets = []
game_over_widgets = []

# プレイヤーの状態
player_y_velocity = 0
on_ground = True

# ゲームの状態
game_state = "START" # "START"スタート画面, "PLAYING"プレイ中, "GAME_OVER"ゲームオーバー時（リザルト）
after_id = None
score = 0
high_scores = []
survival_score_timer = 0 #一秒ごとにスコアを1追加するタイマー

# --- ハイスコア処理 ---
def load_high_scores():
    """ファイルからハイスコアを読み込む"""
    global high_scores
    if not os.path.exists(HIGHSCORE_FILE):
        high_scores = []
        return
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            high_scores = [int(line.strip()) for line in f]
    except (ValueError, FileNotFoundError):
        high_scores = []

def save_high_scores():
    """ハイスコアをファイルに保存する"""
    with open(HIGHSCORE_FILE, "w") as f:
        for s in high_scores:
            f.write(str(s) + "\n")

# --- ゲームロジック関数 ---
def jump(event):
    """スペースキーでプレイヤーをジャンプさせる"""
    global on_ground, player_y_velocity
    if on_ground and game_state == "PLAYING": #プレイヤーが地面と面しているかつゲームをプレイしている状態
        player_y_velocity = JUMP_POWER
        on_ground = False

def update_player():
    """プレイヤーの位置を更新（重力、接地判定）"""
    global on_ground, player_y_velocity
    if player:
        player_y_velocity += GRAVITY
        canvas.move(player, 0, player_y_velocity)
        player_coords = canvas.coords(player)
        if player_coords[3] >= GROUND_Y:
            canvas.coords(player, player_coords[0], GROUND_Y - 50, player_coords[2], GROUND_Y)
            player_y_velocity = 0
            on_ground = True

def create_obstacle():
    """新しい障害物を作成し、コイン生成を試みる"""
    global obstacle
    obstacle_width = 40
    obstacle_height = random.randint(30, 80) #障害物の高さをランダムで決める
    top_y = GROUND_Y - obstacle_height
    obstacle = canvas.create_rectangle(WIDTH, top_y, WIDTH + obstacle_width, GROUND_Y, fill="tomato", outline="")
    
    # 一定の確率でコインも生成する
    if random.random() < COIN_SPAWN_CHANCE:
        create_coin(obstacle_coords=[WIDTH, top_y, WIDTH + obstacle_width, GROUND_Y])

def move_game_objects():
    """障害物とコインを動かす"""
    global obstacle
    if obstacle:
        canvas.move(obstacle, OBSTACLE_SPEED, 0)
        obstacle_coords = canvas.coords(obstacle)
        if obstacle_coords[2] < 0:
            canvas.delete(obstacle)
            obstacle = None
            create_obstacle()
            
    # すべてのコインを動かす
    for coin_id in coins[:]: # リストのコピーをループして、安全に要素を削除
        canvas.move(coin_id, COIN_SPEED, 0)
        if canvas.coords(coin_id)[2] < 0:
            canvas.delete(coin_id)
            coins.remove(coin_id)

def create_coin(obstacle_coords):
    """新しいコインをランダムな位置に作成する"""
    if len(coins) >= MAX_COINS: return # コインが最大数なら作らない

    coin_size = 30
    spawn_pattern = random.choice(['above', 'front_high', 'front_low'])
    
    obstacle_x, obstacle_y_top = obstacle_coords[0], obstacle_coords[1]

    if spawn_pattern == 'above':
        x = obstacle_x + (obstacle_coords[2] - obstacle_coords[0]) / 2 - coin_size / 2
        y = obstacle_y_top - coin_size - random.randint(40, 70)
    elif spawn_pattern == 'front_high':
        x = obstacle_x - random.randint(90, 160)
        y = GROUND_Y - random.randint(140, 200)
    else: # 'front_low'
        x = obstacle_x - random.randint(70, 130)
        y = GROUND_Y - coin_size - 20

    new_coin = canvas.create_oval(x, y, x + coin_size, y + coin_size, fill="gold", outline="")
    coins.append(new_coin)

def check_collisions():
    """当たり判定（障害物とコイン）"""
    global score
    # 障害物との当たり判定
    if player and obstacle:
        p_coords = canvas.coords(player)
        o_coords = canvas.coords(obstacle)
        if p_coords[2] > o_coords[0] and p_coords[0] < o_coords[2] and p_coords[3] > o_coords[1]:
            return "obstacle"
            
    # コインとの当たり判定
    if player:
        p_coords = canvas.coords(player)
        for coin_id in coins[:]:
            c_coords = canvas.coords(coin_id)
            if p_coords[2] > c_coords[0] and p_coords[0] < c_coords[2] and p_coords[3] > c_coords[1] and p_coords[1] < c_coords[3]:
                score += 100
                update_score_display()
                canvas.delete(coin_id)
                coins.remove(coin_id)
    return None

def create_clouds():
    """初期の雲を作成する"""
    for _ in range(3):
        x = random.randint(0, WIDTH)
        y = random.randint(50, 150)
        width = random.randint(50, 100)
        height = random.randint(20, 40)
        cloud_rect = canvas.create_rectangle(x, y, x + width, y + height, fill="white", outline="")
        clouds.append(cloud_rect)

def move_clouds():
    """雲を動かす"""
    for cloud_rect in clouds:
        canvas.move(cloud_rect, CLOUD_SPEED, 0)
        coords = canvas.coords(cloud_rect)
        if coords[2] < 0:
            y = random.randint(50, 150)
            width = random.randint(50, 100)
            height = random.randint(20, 40)
            canvas.coords(cloud_rect, WIDTH, y, WIDTH + width, y + height)

def update_score_display():
    """スコア表示を更新する"""
    canvas.itemconfig(score_text, text=f"スコア: {score}")
    canvas.tag_raise(score_text)

# --- 画面遷移とゲーム状態管理 ---
def clear_screen():
    """キャンバス上の全オブジェクトとUIウィジェットを削除"""
    global player, obstacle, score_text
    # ゲームオブジェクト
    if player: canvas.delete(player)
    if obstacle: canvas.delete(obstacle)
    if score_text: canvas.delete(score_text)
    for coin_id in coins: canvas.delete(coin_id)
    for cloud in clouds: canvas.delete(cloud)
    coins.clear()
    clouds.clear()
    player = obstacle = score_text = None
    # UIウィジェット
    for widget_id in start_screen_widgets + game_over_widgets:
        canvas.delete(widget_id)
    start_screen_widgets.clear()
    game_over_widgets.clear()

def show_start_screen():
    """スタート画面を表示する"""
    global game_state
    game_state = "START"
    clear_screen()
    
    title = canvas.create_text(WIDTH/2, HEIGHT/3, text="ジャンプアクションゲーム", font=("MS Gothic", 40, "bold"), fill="royalblue")
    start_button_widget = tk.Button(root, text="スタート", font=("MS Gothic", 20), command=start_game)
    close_button_widget = tk.Button(root, text="終了", font=("MS Gothic", 20), command=root.destroy)
    
    start_button_window = canvas.create_window(WIDTH/2, HEIGHT/2, window=start_button_widget)
    close_button_window = canvas.create_window(WIDTH/2, HEIGHT/2 + 70, window=close_button_widget)
    
    start_screen_widgets.extend([title, start_button_window, close_button_window])

def start_game():
    """ゲームを開始する"""
    global game_state, player, score, score_text, on_ground, player_y_velocity, survival_score_timer
    game_state = "PLAYING"
    clear_screen()
    
    score = 0
    on_ground = True
    player_y_velocity = 0
    survival_score_timer = 0 #ゲーム開始時にタイマーリセット
    
    player = canvas.create_rectangle(PLAYER_X_START, GROUND_Y - 50, PLAYER_X_START + 50, GROUND_Y, fill="royalblue", outline="")
    score_text = canvas.create_text(WIDTH - 80, 30, text="スコア: 0", font=("MS Gothic", 20, "bold"), fill="gold")
    create_obstacle()
    create_clouds()
    
    game_loop()

def game_over():
    """ゲームオーバー画面を表示する"""
    global game_state, high_scores
    game_state = "GAME_OVER"
    
    high_scores.append(score)
    high_scores = sorted(high_scores, reverse=True)[:5]
    save_high_scores()

    clear_screen()
    
    final_score_text = canvas.create_text(WIDTH/2, HEIGHT/3 - 20, text=f"今回のスコア: {score}", font=("MS Gothic", 30, "bold"), fill="darkblue")
    hs_title = canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text="ハイスコアランキング", font=("MS Gothic", 25, "bold"), fill="black")
    
    game_over_widgets.extend([final_score_text, hs_title])

    for i in range(5):
        rank_text = f"{i+1}位: "
        try:
            rank_text += str(high_scores[i])
        except IndexError:
            rank_text += "-----"
        
        hs_entry = canvas.create_text(WIDTH/2, HEIGHT/2 + i*40, text=rank_text, font=("MS Gothic", 20))
        game_over_widgets.append(hs_entry)

    retry_button_widget = tk.Button(root, text="リトライ", font=("MS Gothic", 20), command=start_game)
    close_button_widget = tk.Button(root, text="終了", font=("MS Gothic", 20), command=root.destroy)

    retry_button_window = canvas.create_window(WIDTH/2, HEIGHT - 100, window=retry_button_widget)
    close_button_window = canvas.create_window(WIDTH/2, HEIGHT - 50, window=close_button_widget)
    
    game_over_widgets.extend([retry_button_window, close_button_window])

def game_loop():
    """メインのゲームループ"""
    global after_id, survival_score_timer, score
    if game_state != "PLAYING":
        return

    update_player()
    move_game_objects()
    move_clouds()
    
    survival_score_timer += 1 #生存時間のカウント

    if survival_score_timer >= FRAMES_PER_SECOND: #一秒たったらスコア＋１、生存時間のカウントを0に戻す
        score += 1
        survival_score_timer = 0
        update_score_display()
    
    collision_type = check_collisions()
    if collision_type == "obstacle":
        game_over()
    else:
        after_id = root.after(1000 // FRAMES_PER_SECOND, game_loop)

# --- UIのセットアップ ---
root = tk.Tk()
root.title("ジャンプアクションゲーム")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="skyblue")
canvas.pack()

canvas.create_rectangle(0, GROUND_Y, WIDTH, HEIGHT, fill="olivedrab", outline="")

root.bind("<space>", jump)

# --- アプリケーションの開始 ---
load_high_scores()
show_start_screen()
root.mainloop()
