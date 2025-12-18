import streamlit as st
import matplotlib.pyplot as plt
import numpy as np # 我們需要這個來切分梁的座標

# --- 1. 土木核心邏輯 (計算引擎) ---
class SimpleBeam:
    def __init__(self, length):
        self.length = length
        self.loads = []

    def add_point_load(self, P, x):
        self.loads.append({"type": "point", "P": P, "x": x})

    def solve_reactions(self):
        """ 計算支承反力 """
        sum_moment_A = 0
        total_load = 0
        for load in self.loads:
            sum_moment_A += load["P"] * load["x"]
            total_load += load["P"]
        
        rb = sum_moment_A / self.length
        ra = total_load - rb
        return ra, rb

    def calculate_internal_forces(self, ra, rb):
        """ 
        核心算法：切面法 (Method of Sections)
        我們把梁切成 500 個點，算出每個點的 V 和 M
        """
        # 建立 x 座標陣列 (從 0 到 L，共 500 個點)
        x_coords = np.linspace(0, self.length, 500)
        shear_forces = []
        bending_moments = []

        for x in x_coords:
            # 初始化：從左邊切開，先看到左支承 Ra
            V = ra
            M = ra * x 

            # 檢查這個切面左邊有沒有載重
            for load in self.loads:
                if x > load["x"]: # 如果切面在載重的右邊，就要扣掉載重
                    V -= load["P"]
                    M -= load["P"] * (x - load["x"]) # 力臂是 (x - 載重位置)
            
            shear_forces.append(V)
            bending_moments.append(M)
            
        return x_coords, shear_forces, bending_moments

# --- 2. 繪圖引擎 (升級版：一次畫三張圖) ---
def plot_analysis(beam, ra, rb, x_vals, V_vals, M_vals):
    # 建立 3 張子圖 (Subplots)，共用 X 軸
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    
    # === 圖 1: 自由體圖 (FBD) ===
    ax1.set_title("1. 自由體圖 (FBD)", fontsize=12, loc='left')
    ax1.plot([0, beam.length], [0, 0], color='black', linewidth=5) # 梁本體
    # 支承
    ax1.plot(0, -0.2, marker='^', markersize=15, color='grey')
    ax1.text(0, -0.8, f"Ra={ra:.1f}", ha='center', color='blue', fontweight='bold')
    ax1.plot(beam.length, -0.2, marker='o', markersize=15, color='grey')
    ax1.text(beam.length, -0.8, f"Rb={rb:.1f}", ha='center', color='blue', fontweight='bold')
    # 載重
    for load in beam.loads:
        ax1.arrow(load["x"], 1.5, 0, -1.0, head_width=0.3, fc='red', ec='red')
        ax1.text(load["x"], 1.8, f"P={load['P']}", ha='center', color='red')
    ax1.set_ylim(-1.5, 2.5)
    ax1.axis('off') # 隱藏座標軸框線

    # === 圖 2: 剪力圖 (SFD) ===
    ax2.set_title("2. 剪力圖 (Shear Force Diagram)", fontsize=12, loc='left')
    ax2.plot(x_vals, V_vals, color='green', linewidth=2)
    ax2.fill_between(x_vals, V_vals, 0, color='green', alpha=0.1) # 填色
    ax2.set_ylabel("Shear (kN)")
    ax2.grid(True, linestyle='--', alpha=0.5)
    # 標示最大值
    max_v = max(map(abs, V_vals))
    ax2.text(0, max_v, f"Max V: {max_v:.1f}", color='green', fontweight='bold')

    # === 圖 3: 彎矩圖 (BMD) ===
    ax3.set_title("3. 彎矩圖 (Bending Moment Diagram)", fontsize=12, loc='left')
    ax3.plot(x_vals, M_vals, color='orange', linewidth=2)
    ax3.fill_between(x_vals, M_vals, 0, color='orange', alpha=0.1) # 填色
    ax3.set_ylabel("Moment (kN-m)")
    ax3.set_xlabel("Position (m)")
    ax3.grid(True, linestyle='--', alpha=0.5)
    # 標示最大值
    max_m = max(M_vals)
    ax3.text(beam.length/2, max_m, f"Max M: {max_m:.1f}", color='orange', fontweight='bold')

    plt.tight_layout()
    return fig

# --- 3. 網頁介面 ---
st.set_page_config(page_title="梁之試煉 Level 2", page_icon="🏗️")

st.title("🏗️ 土木結構分析：SFD & BMD")
st.markdown("### 拖動滑桿，觀察剪力圖與彎矩圖的變化！")

# 側邊欄
with st.sidebar:
    st.header("參數設定")
    L = st.slider("梁長度 (m)", 5.0, 20.0, 10.0)
    P = st.number_input("集中載重 P (kN)", value=100.0)
    x_p = st.slider("載重位置 x (m)", 0.0, L, L/2.0)

# 計算流程
beam = SimpleBeam(L)
beam.add_point_load(P, x_p)
ra, rb = beam.solve_reactions()
x_vals, V_vals, M_vals = beam.calculate_internal_forces(ra, rb)

# 顯示數據
c1, c2, c3 = st.columns(3)
c1.metric("左支承 Ra", f"{ra:.1f} kN")
c2.metric("右支承 Rb", f"{rb:.1f} kN")
c3.metric("最大彎矩 Mmax", f"{max(M_vals):.1f} kN-m")

# 顯示圖表
fig = plot_analysis(beam, ra, rb, x_vals, V_vals, M_vals)
st.pyplot(fig)