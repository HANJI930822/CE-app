import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['DFKai-SB'] # 設定使用「標楷體」
plt.rcParams['axes.unicode_minus'] = False     # 讓負號正常顯示

# --- 1. 升級版物理引擎 (支援 UDL) ---
class BeamLevel2:
    def __init__(self, length):
        self.length = length
        # 這裡我們簡化：一個集中載重 + 一個均佈載重
        self.point_load = {"P": 0, "x": 0} 
        self.udl = {"w": 0, "start": 0, "end": 0} # w 是單位重 (kN/m)

    def set_loads(self, P, x_p, w, w_start, w_end):
        self.point_load = {"P": P, "x": x_p}
        self.udl = {"w": w, "start": w_start, "end": w_end}

    def solve_analysis(self):
        L = self.length
        
        # A. 計算支承反力 (Reactions)
        # 1. 集中載重造成的力矩
        moment_from_point = self.point_load["P"] * self.point_load["x"]
        
        # 2. 均佈載重造成的力矩 (把它當成合力作用在中心點)
        udl_total_force = self.udl["w"] * (self.udl["end"] - self.udl["start"])
        udl_center = (self.udl["start"] + self.udl["end"]) / 2
        moment_from_udl = udl_total_force * udl_center
        
        # 3. 計算反力
        rb = (moment_from_point + moment_from_udl) / L
        ra = (self.point_load["P"] + udl_total_force) - rb
        
        # B. 切面法計算 SFD & BMD (切 500 等份)
        x_vals = np.linspace(0, L, 500)
        V_vals = []
        M_vals = []
        
        for x in x_vals:
            # 初始值 (左支承)
            V = ra
            M = ra * x
            
            # 扣除集中載重
            if x > self.point_load["x"]:
                V -= self.point_load["P"]
                M -= self.point_load["P"] * (x - self.point_load["x"])
            
            # 扣除均佈載重 (積分觀念)
            # 只有當 x 進入均佈載重範圍才開始扣
            if x > self.udl["start"]:
                # 計算「已經走過」的均佈載重長度
                cover_len = min(x, self.udl["end"]) - self.udl["start"]
                if cover_len > 0:
                    force_segment = self.udl["w"] * cover_len
                    # 力臂 = x - (該段載重的中心)
                    moment_arm = x - (self.udl["start"] + cover_len/2)
                    
                    V -= force_segment
                    M -= force_segment * moment_arm
            
            V_vals.append(V)
            M_vals.append(M)
            
        return ra, rb, x_vals, V_vals, M_vals

# --- 2. 繪圖函數 ---
def plot_level2(beam, ra, rb, x_vals, V_vals, M_vals):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    
    # 圖1: FBD
    ax1.set_title("1. 自由體圖 (FBD) - 包含均佈載重", loc='left')
    ax1.plot([0, beam.length], [0, 0], 'k-', lw=5)
    ax1.plot(0, -0.5, '^', ms=15, color='grey'); ax1.text(0, -1.5, f"Ra={ra:.1f}", color='blue')
    ax1.plot(beam.length, -0.5, 'o', ms=15, color='grey'); ax1.text(beam.length, -1.5, f"Rb={rb:.1f}", color='blue')
    
    # 畫集中載重
    if beam.point_load["P"] > 0:
        ax1.arrow(beam.point_load["x"], 2, 0, -1.5, head_width=0.3, fc='red', ec='red')
        ax1.text(beam.point_load["x"], 2.5, f"P={beam.point_load['P']}", ha='center', color='red')
        
    # 畫均佈載重 (用一排藍色小箭頭表示)
    if beam.udl["w"] > 0:
        start, end = beam.udl["start"], beam.udl["end"]
        # 畫一條橫槓
        ax1.plot([start, end], [1.5, 1.5], color='blue', lw=2)
        ax1.text((start+end)/2, 2.0, f"w={beam.udl['w']} kN/m", ha='center', color='blue')
        # 畫下面的小箭頭
        for arrow_x in np.linspace(start, end, int((end-start)*2) + 2):
            ax1.arrow(arrow_x, 1.5, 0, -1.0, head_width=0.1, color='blue', alpha=0.5)

    ax1.set_ylim(-2, 4)
    ax1.axis('off')

    # 圖2: SFD
    ax2.set_title("2. 剪力圖 (注意斜直線)", loc='left')
    ax2.plot(x_vals, V_vals, 'g-', lw=2)
    ax2.fill_between(x_vals, V_vals, 0, color='green', alpha=0.1)
    ax2.set_ylabel("V (kN)")
    ax2.grid(True, ls='--', alpha=0.5)

    # 圖3: BMD
    ax3.set_title("3. 彎矩圖 (注意拋物線)", loc='left')
    ax3.plot(x_vals, M_vals, color='orange', lw=2)
    ax3.fill_between(x_vals, M_vals, 0, color='orange', alpha=0.1)
    ax3.set_ylabel("M (kN-m)")
    ax3.set_xlabel("Position (m)")
    ax3.grid(True, ls='--', alpha=0.5)

    return fig

# --- 3. 頁面介面 ---
st.set_page_config(page_title="Level 2: 均佈載重", page_icon="🌊")

st.title("Level 2: 均佈載重 (Distributed Load)")
st.info("💡 觀察重點：當剪力圖呈現「斜直線」時，彎矩圖會呈現「拋物線」！")

with st.sidebar:
    st.header("參數設定")
    L = st.slider("梁長度", 5.0, 20.0, 10.0)
    
    st.subheader("🔴 集中載重 (Point Load)")
    P = st.number_input("P (kN)", value=50.0)
    x_p = st.slider("位置 x_p", 0.0, L, L/2)
    
    st.subheader("🔵 均佈載重 (UDL)")
    w = st.number_input("w (kN/m)", value=10.0)
    # 讓使用者選範圍，預設是全梁滿載
    w_range = st.slider("分佈範圍 (Start - End)", 0.0, L, (0.0, L))

# 計算
beam = BeamLevel2(L)
beam.set_loads(P, x_p, w, w_range[0], w_range[1])
ra, rb, xs, Vs, Ms = beam.solve_analysis()

# 顯示
c1, c2, c3 = st.columns(3)
c1.metric("Ra", f"{ra:.1f}")
c2.metric("Rb", f"{rb:.1f}")
c3.metric("Max Moment", f"{max(Ms):.1f}")

st.pyplot(plot_level2(beam, ra, rb, xs, Vs, Ms))