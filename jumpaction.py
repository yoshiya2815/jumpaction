import tkinter as tk
import random
import os

# --- ゲームの定数 ---
# これらの値はゲームのバランスを調整するために使われる
WIDTH = 800  # 画面の幅
HEIGHT = 600 # 画面の高さ
GROUND_Y = 450 # 地面のY座標
GRAVITY = 1.2      # プレイヤーにかかる重力
JUMP_POWER = -20   # ジャンプの強さ（マイナスが大きいほど高く飛ぶ）
PLAYER_X_START = 100 # プレイヤーの初期X座標
OBSTACLE_SPEED = -10 # 障害物の移動速度
CLOUD_SPEED = -3     # 雲の移動速度（奥行きを出すために遅くする）
COIN_SPEED = -10     # コインの移動速度
COIN_SPAWN_PROBABILITY_PER_SECOND = 0.5 # 1秒ごとにコインが出現する確率
MAX_COINS = 2 # 画面上に同時に存在できるコインの最大数
HIGHSCORE_FILE = "highscores.txt" # ハイスコアを保存するファイル名
FRAMES_PER_SECOND = 60 # 1秒あたりのフレーム更新数（ゲームの滑らかさを決める）
GET_COIN_SCORE = 100

# --- グローバル変数 ---
# これらの変数は複数の関数で共有して使うため、グローバル領域で定義する
# オブジェクトID
player = None
obstacle = None
coins = [] # 複数のコインをリストで管理
clouds = []
score_text = None

# UI要素のID
start_screen_widgets = []
game_over_widgets = []

# プレイヤーの状態
player_y_velocity = 0 # プレイヤーのY軸方向の速度
on_ground = True      # プレイヤーが地面にいるかどうか

# ゲームの状態
game_state = "START" # "START", "PLAYING", "GAME_OVER" のいずれか
after_id = None      # ゲームループのID（停止させるために必要）
score = 0
high_scores = []
survival_score_timer = 0
difficulty_level = 0
speed_up_text_id = None

# --- ハイスコア処理 ---
def load_high_scores():
    """
    ゲーム開始時に、ファイルから過去のハイスコアを読み込む。
    ファイルが存在しない、または内容が不正な場合は、空のリストとして扱う。
    """
    global high_scores
    # ファイルが存在しない場合は、何もせず終了
    if not os.path.exists(HIGHSCORE_FILE):
        high_scores = []
        return
    # ファイルの読み込み中にエラーが発生してもプログラムが落ちないように、try-exceptで保護する
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            # ファイルから一行ずつ読み込み、数値に変換してリストに格納
            high_scores = [int(line.strip()) for line in f]
    except (ValueError, FileNotFoundError):
        # ファイルが空だったり、文字が混ざっていた場合は、スコアをリセット
        high_scores = []

def save_high_scores():
    """現在のハイスコアリストをファイルに上書き保存する"""
    with open(HIGHSCORE_FILE, "w") as f:
        for s in high_scores:
            f.write(str(s) + "\n")

# --- ゲームロジック関数 ---
def jump(event):
    """スペースキーが押されたときにプレイヤーをジャンプさせる"""
    global on_ground, player_y_velocity
    # ジャンプできるのは、地面にいて、かつプレイ中のときのみ
    if on_ground and game_state == "PLAYING":
        player_y_velocity = JUMP_POWER # Y軸の速度に上向きの力を加える
        on_ground = False # ジャンプ中は地面にいない状態にする

def update_player():
    """プレイヤーの位置を更新する（物理演算）"""
    global on_ground, player_y_velocity
    if player:
        # 1. 重力計算: 常に下向きの力を速度に加える
        player_y_velocity += GRAVITY
        # 2. 移動: 計算された速度に応じてプレイヤーを動かす
        canvas.move(player, 0, player_y_velocity)
        
        player_coords = canvas.coords(player)
        
        # 3. 接地判定: プレイヤーが地面より下にめり込まないようにする処理
        if player_coords[3] >= GROUND_Y:
            # プレイヤーの位置を地面の高さに補正
            canvas.coords(player, player_coords[0], GROUND_Y - 50, player_coords[2], GROUND_Y)
            player_y_velocity = 0 # 落下速度をリセット
            on_ground = True      # 地面にいる状態に戻す

def create_obstacle():
    """新しい障害物を画面右端に作成する"""
    global obstacle, difficulty_level
    max_obstacle_width = 40 + difficulty_level * 20
    obstacle_width = random.randint(40, max_obstacle_width)
    # ゲームが単調にならないよう、障害物の高さを毎回ランダムにする
    obstacle_height = random.randint(30, 80)
    top_y = GROUND_Y - obstacle_height
    # 画面外(WIDTH)から出現させ、自然にスクロールインさせる
    obstacle = canvas.create_rectangle(WIDTH, top_y, WIDTH + obstacle_width, GROUND_Y, fill="tomato", outline="")

def move_game_objects():
    """障害物とコインを左に動かす"""
    global obstacle
    # --- 障害物の移動 ---
    if obstacle:
        canvas.move(obstacle, OBSTACLE_SPEED, 0)
        # 画面外に出たかどうかの判定
        if canvas.coords(obstacle)[2] < 0:
            canvas.delete(obstacle)
            obstacle = None # 存在しない状態にする
            create_obstacle() # 新しい障害物を作成する
            
    # --- コインの移動 ---
    # forループ中にリストから要素を削除するとエラーの原因になるため、
    # リストのコピー `coins[:]` を使って安全にループ処理を行う
    for coin_id in coins[:]:
        canvas.move(coin_id, COIN_SPEED, 0)
        # 画面外に出たら、オブジェクトとリストから削除
        if canvas.coords(coin_id)[2] < 0:
            canvas.delete(coin_id)
            coins.remove(coin_id)

def create_coin():
    """新しいコインをランダムな高さで作成する"""
    # 画面上のコインが最大数に達している場合は、何もしない
    if len(coins) >= MAX_COINS: return

    coin_size = 30
    x = WIDTH # 常に画面右端から出現
    # 出現する高さ（Y座標）をランダムに決定
    y = GROUND_Y - random.randint(60, 200)

    new_coin = canvas.create_oval(x, y, x + coin_size, y + coin_size, fill="gold", outline="")
    coins.append(new_coin)

def check_collisions():
    """
    プレイヤーと他のゲームオブジェクト（障害物、コイン）との当たり判定をまとめて行う。
    衝突を検知した場合は、適切な処理を呼び出す。
    """
    global score # スコアを管理するグローバル変数を変更するために宣言

    # --- 障害物との当たり判定 ---
    # プレイヤーと障害物の両方が存在する場合のみ、判定処理を行う
    if player and obstacle:
        # 各オブジェクトの現在座標 [x1, y1, x2, y2] を取得
        p_coords = canvas.coords(player)
        o_coords = canvas.coords(obstacle)

        # 矩形（四角形）同士の当たり判定ロジック
        # 以下の4つの条件がすべて真のとき、オブジェクトは重なっていると判断できる
        # 1. プレイヤーの右端 > 障害物の左端
        # 2. プレイヤーの左端 < 障害物の右端
        # 3. プレイヤーの下端 > 障害物の上端
        # (今回はプレイヤーが障害物の上を飛び越えるため、プレイヤーの上端と障害物の下端の比較は不要)
        if p_coords[2] > o_coords[0] and p_coords[0] < o_coords[2] and p_coords[3] > o_coords[1]:
            # 障害物に当たったことを示す文字列を返す
            return "obstacle"
            
    # --- コインとの当たり判定 ---
    # プレイヤーが存在する場合のみ、判定処理を行う
    if player:
        p_coords = canvas.coords(player)
        
        # forループ中にリストから要素を削除するとエラーの原因になるため、
        # リストのコピー `coins[:]` を使って安全にループ処理を行う
        for coin_id in coins[:]:
            c_coords = canvas.coords(coin_id)

            # コインとの当たり判定ロジック（障害物判定に加えて、上下の判定も行う）
            # 1. プレイヤーの右端 > コインの左端
            # 2. プレイヤーの左端 < コインの右端
            # 3. プレイヤーの下端 > コインの上端
            # 4. プレイヤーの上端 < コインの下端
            if p_coords[2] > c_coords[0] and p_coords[0] < c_coords[2] and p_coords[3] > c_coords[1] and p_coords[1] < c_coords[3]:
                # スコアを加算し、画面表示を更新
                score += GET_COIN_SCORE
                update_score_display()
                
                # 取得したコインを画面から削除
                canvas.delete(coin_id)
                # 管理リストからも削除
                coins.remove(coin_id)
                
    # 何にも衝突しなかった場合はNone（なし）を返す
    return None


def create_clouds():
    """ゲーム開始時に、背景の雲をいくつか初期配置する"""
    for _ in range(3):
        x = random.randint(0, WIDTH)
        y = random.randint(50, 150)
        width = random.randint(50, 100)
        height = random.randint(20, 40)
        cloud_rect = canvas.create_rectangle(x, y, x + width, y + height, fill="white", outline="")
        clouds.append(cloud_rect)

def move_clouds():
    """すべての雲を動かし、画面外に出たら再配置する"""
    for cloud_rect in clouds:
        # 雲はゆっくり動かすことで、遠くにあるように見せ、奥行きを表現する
        canvas.move(cloud_rect, CLOUD_SPEED, 0)
        coords = canvas.coords(cloud_rect)
        # 画面の左端に完全に消えたら
        if coords[2] < 0:
            # 新しい雲を作るのではなく、既存の雲を画面右端に再配置して使い回す（効率化）
            y = random.randint(50, 150)
            width = random.randint(50, 100)
            height = random.randint(20, 40)
            canvas.coords(cloud_rect, WIDTH, y, WIDTH + width, y + height)

def increase_difficulty():
    "条件を満たすことで難易度（スピード）が上昇する"
    global difficulty_level, OBSTACLE_SPEED, CLOUD_SPEED, COIN_SPEED, speed_up_text_id

    #難易度レベルの上昇
    difficulty_level += 1

    #障害物、雲、コインのスピードを上げる（右から左へ行くためー）
    OBSTACLE_SPEED -= 2
    CLOUD_SPEED -= 1
    COIN_SPEED -= 2

    #テキストが残っていれば消す
    if speed_up_text_id:
        canvas.delete(speed_up_text_id)
    
    #スピードアップの文字を2秒間表示
    speed_up_text_id = canvas.create_text(WIDTH/2, 200, text="Speed UP!!", font=("MS Gothic", 40, "bold"), fill="orange")
    canvas.after(2000, lambda: canvas.delete(speed_up_text_id) if speed_up_text_id else None)

def update_score_display():
    """画面右上のスコア表示を現在のスコアで更新する"""
    canvas.itemconfig(score_text, text=f"スコア: {score}")
    # スコアが雲などの後ろに隠れないように、常に最前面に表示する
    canvas.tag_raise(score_text)

# --- 画面遷移とゲーム状態管理 ---
def clear_screen():
    """次の画面に遷移する前に、キャンバス上の全オブジェクトとUIウィジェットを削除する"""
    global player, obstacle, score_text
    # 1. ゲームオブジェクトの削除
    if player: canvas.delete(player)
    if obstacle: canvas.delete(obstacle)
    if score_text: canvas.delete(score_text)
    for coin_id in coins: canvas.delete(coin_id)
    for cloud in clouds: canvas.delete(cloud)
    coins.clear(); clouds.clear() # 管理リストも空にする
    player = obstacle = score_text = None
    
    # 2. ボタンなどのUIウィジェットの削除
    for widget_id in start_screen_widgets + game_over_widgets:
        canvas.delete(widget_id)
    start_screen_widgets.clear(); game_over_widgets.clear()

def show_start_screen():
    """スタート画面のUIを作成・表示する"""
    global game_state
    game_state = "START"
    clear_screen()
    
    title = canvas.create_text(WIDTH/2, HEIGHT/3, text="ジャンプアクションゲーム", font=("MS Gothic", 40, "bold"), fill="royalblue")
    start_button_widget = tk.Button(root, text="スタート", font=("MS Gothic", 20), command=start_game)
    close_button_widget = tk.Button(root, text="終了", font=("MS Gothic", 20), command=root.destroy)
    
    # tkinterのボタンはCanvasのcreate_windowを使って配置する
    start_button_window = canvas.create_window(WIDTH/2, HEIGHT/2, window=start_button_widget)
    close_button_window = canvas.create_window(WIDTH/2, HEIGHT/2 + 70, window=close_button_widget)
    
    # 後でまとめて削除できるように、ウィジェットのIDをリストに保存しておく
    start_screen_widgets.extend([title, start_button_window, close_button_window])

def start_game():
    """ゲームプレイを開始するための初期化処理"""
    global game_state, player, score, score_text, on_ground, player_y_velocity, survival_score_timer, OBSTACLE_SPEED, CLOUD_SPEED, COIN_SPEED, difficulty_level
    game_state = "PLAYING"
    clear_screen()
    
    # ゲーム関連の変数をすべて初期値にリセット
    score = 0
    on_ground = True
    player_y_velocity = 0
    survival_score_timer = 0
    OBSTACLE_SPEED = -10
    CLOUD_SPEED = -3
    COIN_SPEED = -10
    difficulty_level = 0

    # プレイヤーや障害物などのオブジェクトを生成
    player = canvas.create_rectangle(PLAYER_X_START, GROUND_Y - 50, PLAYER_X_START + 50, GROUND_Y, fill="royalblue", outline="")
    score_text = canvas.create_text(WIDTH - 20, 30, text="スコア: 0", font=("MS Gothic", 20, "bold"), fill="gold", anchor=tk.NE)
    create_obstacle()
    create_clouds()
    
    # ゲームループを開始
    game_loop()

def game_over():
    """ゲームオーバー時の処理とリザルト画面の表示"""
    global game_state, high_scores
    game_state = "GAME_OVER"
    
    # ハイスコアの更新と保存
    high_scores.append(score)
    high_scores = sorted(high_scores, reverse=True)[:5] # 上位5件のみ残す
    save_high_scores()

    clear_screen()
    
    # --- リザルト画面の描画 ---
    final_score_text = canvas.create_text(WIDTH/2, HEIGHT/3 - 20, text=f"今回のスコア: {score}", font=("MS Gothic", 30, "bold"), fill="darkblue")
    hs_title = canvas.create_text(WIDTH/2, HEIGHT/2 - 40, text="ハイスコアランキング", font=("MS Gothic", 25, "bold"), fill="black")
    game_over_widgets.extend([final_score_text, hs_title])

    # ハイスコアランキングを表示
    for i in range(5):
        rank_text = f"{i+1}位: "
        # スコアが存在しない順位は "-----" と表示する
        try:
            rank_text += str(high_scores[i])
        except IndexError:
            rank_text += "-----"
        hs_entry = canvas.create_text(WIDTH/2, HEIGHT/2 + i*40, text=rank_text, font=("MS Gothic", 20))
        game_over_widgets.append(hs_entry)

    # リトライボタンと終了ボタンを配置
    retry_button_widget = tk.Button(root, text="リトライ", font=("MS Gothic", 20), command=start_game)
    close_button_widget = tk.Button(root, text="終了", font=("MS Gothic", 20), command=root.destroy)
    retry_button_window = canvas.create_window(WIDTH/2, HEIGHT - 100, window=retry_button_widget)
    close_button_window = canvas.create_window(WIDTH/2, HEIGHT - 50, window=close_button_widget)
    game_over_widgets.extend([retry_button_window, close_button_window])

def game_loop():
    """ゲームのメインループ。約1/60秒ごとに繰り返し実行される"""
    global after_id, survival_score_timer, score
    if game_state != "PLAYING":
        return

    # 1. 各オブジェクトの状態を更新
    update_player()
    move_game_objects()
    move_clouds()
    
    # 2. サバイバルスコアと時間ベースのイベントを処理
    survival_score_timer += 1
    # 1秒（=FRAMES_PER_SECOND回ループ）経過したか判定
    if survival_score_timer >= FRAMES_PER_SECOND:
        score += 1 # サバイバルスコアを加算
        survival_score_timer = 0 # タイマーをリセット
        update_score_display()
        # 一定確率でコインを生成
        if random.random() < COIN_SPAWN_PROBABILITY_PER_SECOND:
            create_coin()
    
    #　難易度上昇
    if score // 1000 > difficulty_level:
        increase_difficulty()

    # 3. 衝突判定
    collision_type = check_collisions()
    if collision_type == "obstacle":
        game_over() # 障害物に当たったらゲームオーバー
    else:
        # 4. 次のフレームを予約
        after_id = root.after(1000 // FRAMES_PER_SECOND, game_loop)

# --- UIのセットアップ ---
root = tk.Tk()
root.title("ジャンプアクションゲーム")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False) # ウィンドウサイズを固定

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="skyblue")
canvas.pack()

# 地面を描画
canvas.create_rectangle(0, GROUND_Y, WIDTH, HEIGHT, fill="olivedrab", outline="")

# スペースキーが押されたらjump関数を呼び出すように設定
root.bind("<space>", jump)

# --- アプリケーションの開始 ---
load_high_scores()    # ハイスコアを読み込む
show_start_screen()   # スタート画面を表示
root.mainloop()       # ウィンドウの表示とイベント待機を開始
