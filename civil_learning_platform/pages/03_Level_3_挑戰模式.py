import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import random # 這是亂數產生器，用來出題

# --- 1. 設定字體 (標楷體) ---
plt.rcParams['font.sans-serif'] = ['DFKai-SB']
plt.rcParams['axes.unicode_minus'] = False

# --- 2. 核心計算邏輯 (跟 Level 1 一樣) ---
def solve_beam(L, P, x):
    # Ra + Rb = P
    # Sum M_A = 0 => P*x - Rb*L = 0 => Rb = P*x / L
    rb = P * x / L
    ra = P - rb
    return ra, rb

def plot_answer(L, P, x, ra, rb):
    # 這裡我們只畫 SFD 和 BMD 當作獎勵
    x_vals = np.linspace(0, L, 500)
    V_vals = []
    M_vals = []
    
    for val in x_vals:
        V = ra
        M = ra * val
        if val > x:
            V -= P
            M -= P * (val - x)
        V_vals.append(V)
        M_vals.append(M)
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    
    # SFD
    ax1.set_title("剪力圖 (SFD)", loc='left')
    ax1.plot(x_vals, V_vals, 'g-', lw=2)
    ax1.fill_between(x_vals, V_vals, 0, color='green', alpha=0.1)
    ax1.text(0, max(V_vals), f"Max V={max(V_vals):.1f}", color='green')
    ax1.grid(True, ls='--')
    
    # BMD
    ax2.set_title("彎矩圖 (BMD)", loc='left')
    ax2.plot(x_vals, M_vals, 'orange', lw=2)
    ax2.fill_between(x_vals, M_vals, 0, color='orange', alpha=0.1)
    ax2.text(x, max(M_vals), f"Max M={max(M_vals):.1f}", color='orange')
    ax2.set_xlabel("位置 (m)")
    ax2.grid(True, ls='--')
    
    return fig

# --- 3. 頁面介面 (遊戲邏輯) ---
st.set_page_config(page_title="Level 3: 執照考驗", page_icon="⚔️")

st.title("⚔️ Level 3: 結構技師隨堂考")
st.markdown("系統將**隨機出題**，請拿出紙筆計算，通過考驗才能解鎖圖表！")

# --- 關鍵技術：Session State (記憶體) ---
# 我們需要讓網頁「記住」現在的題目是什麼，不然每次按按鈕題目都會變

if 'exam_data' not in st.session_state:
    # 如果記憶體裡沒有題目，就初始化一題
    st.session_state.exam_data = {
        "L": 10.0, # 預設值
        "P": 100.0,
        "x": 5.0,
        "has_generated": False # 標記是否已經生成過亂數
    }

# --- 介面區 ---

col_btn, col_info = st.columns([1, 2])

with col_btn:
    # 按鈕：生成新題目
    if st.button("🎲 生成新題目 / 重置"):
        # 產生亂數 (L: 5~20, P: 10~200, x: 1~L-1)
        new_L = random.randint(5, 20)
        new_P = random.randint(10, 200) * 1.0
        new_x = random.randint(1, new_L - 1) * 1.0
        
        # 存入記憶體
        st.session_state.exam_data = {
            "L": float(new_L),
            "P": new_P,
            "x": new_x,
            "has_generated": True
        }
        # 清除之前的作答紀錄 (如果有用到可以清，這邊先簡單處理)
        st.rerun() # 重新整理頁面

# 讀取當前的題目
current_L = st.session_state.exam_data["L"]
current_P = st.session_state.exam_data["P"]
current_x = st.session_state.exam_data["x"]

# 顯示題目 (視覺化)
st.subheader("📋 題目卷：")
st.info(f"有一根長度 **{current_L} m** 的簡支梁，在距離左端 **{current_x} m** 處受到 **{current_P} kN** 的集中載重。")

# 簡單畫個示意圖 (只有幾何，沒有答案)
fig_q, ax_q = plt.subplots(figsize=(8, 2))
ax_q.plot([0, current_L], [0, 0], 'k-', lw=5)
ax_q.plot(0, -0.2, '^', ms=15, color='grey'); ax_q.text(0, -0.8, "Ra=?", color='red', fontsize=14)
ax_q.plot(current_L, -0.2, 'o', ms=15, color='grey'); ax_q.text(current_L, -0.8, "Rb=?", color='red', fontsize=14)
ax_q.arrow(current_x, 1.5, 0, -1.0, head_width=0.3, fc='black', ec='black')
ax_q.text(current_x, 1.8, f"P={current_P}", ha='center')
ax_q.set_ylim(-1, 2.5); ax_q.axis('off')
st.pyplot(fig_q)

st.write("---")

# 作答區
st.subheader("✍️ 請作答：")
c1, c2 = st.columns(2)
user_ra = c1.number_input("你算出的 Ra (kN)", value=0.0, step=1.0)
user_rb = c2.number_input("你算出的 Rb (kN)", value=0.0, step=1.0)

# 送出按鈕
if st.button("🚀 送出答案"):
    # 電腦偷偷算正確答案
    true_ra, true_rb = solve_beam(current_L, current_P, current_x)
    
    # 判定對錯 (允許 0.1 的誤差)
    is_correct_ra = abs(user_ra - true_ra) < 0.1
    is_correct_rb = abs(user_rb - true_rb) < 0.1
    
    if is_correct_ra and is_correct_rb:
        st.balloons() # 放氣球慶祝！
        st.success("🎉 太神啦！完全正確！你已經具備結構技師的潛力了！")
        
        # 答對了才給看詳細圖表 (獎勵)
        with st.expander("點擊查看詳細分析圖 (SFD & BMD)", expanded=True):
            fig_ans = plot_answer(current_L, current_P, current_x, true_ra, true_rb)
            st.pyplot(fig_ans)
    else:
        st.error("💥 崩塌警報！計算錯誤，請重新檢查力矩平衡！")
        if not is_correct_ra:
            st.warning(f"❌ Ra 算錯了... (提示：對右支承取力矩試試看)")
        if not is_correct_rb:
            st.warning(f"❌ Rb 算錯了...")