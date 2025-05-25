import streamlit as st
import pandas as pd
import numpy as np
import math
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="透析室面積")
st.title("透析室面積計算")

# --- 入力部分 ---
input_num = st.number_input('一か月の透析患者数を入力してください', value=0)

# --- 面積計算ロジック ---
# 一日の入院患者数を計算（透析の場合は30日で割る）
month_patients = math.ceil(input_num / 30)

# 昼間9割り、夜間1割りとして換算し、3ベッドをバッファとしています。外来患者が多い病院では調整をしてください。
# 透析センター　月水金（午前・午後）、火木土（午前・午後）の4クール体制を基本とし、＋夜間透析がある想定。
day_patients = math.ceil(month_patients *0.45 + 3)

# 透析室の広さ　ベッド廻りとベッド足元の通路の面積を計算しています。イメージは　ベッドサイドに物入れ、頭側に透析装置、足元はカーテン引ける位。ちょっと大きいので個室が10%位入る。今後改善
# 感染対策を重視する病院は少し大きくしてください
bed_area = math.ceil(day_patients * 5.8 + day_patients * 1.5)

#付属室の計算
#機械室/ベッド数に合わせて容量を算出。段階で分ける。故障に備え２台タンク運用を想定。
machineroom_size = math.ceil(day_patients) * 1.2

#機械室横倉庫/輸液などを置く倉庫。ベッド数に合わせて容量を算出。段階で分ける。
warehouse_size = math.ceil(machineroom_size/2)

# スタッフ数　
# ベッド数に合わせて配置。段階で分ける。
num_stuff = day_patients * 0.3 + 1

stuffstation_area = num_stuff * 6.5 + 5

#器材庫/スタッフ数で算出
warehouse_size2 = math.ceil(stuffstation_area/5)

#スタッフ休憩室
stuff_hos = math.ceil(num_stuff*2)

#汚物処理室
obutu = math.ceil(6)

#患者便所
resutroom = math.ceil(4)

#患者休憩室
hosupital_area = math.ceil(day_patients*3)

#更衣室
kouisitu = math.ceil(day_patients/3*1.2*2)


# --- 柱の面積を計算する関数 (間隔7m固定) ---
def calculate_pillar_area_fixed_spacing(total_area):
    """
    指定された総面積と7m固定の間隔に基づいて、想定される柱の総面積を計算する関数。

    縦横の長さは7mの倍数に調整され、なるべく正方形に近い形状を優先します。
    柱1本あたりの面積は0.9m²と仮定します。

    :param total_area: 敷地の総面積 (平方メートル)
    :return: hashira_area - 柱の総面積 (平方メートル)
    """
    fixed_spacing = 7  # 柱の間隔を7mで固定
    area_per_pillar = 0.9  # 柱1本あたりの面積 (m²)

    estimated_side = math.sqrt(total_area)
    length = math.ceil(estimated_side / fixed_spacing) * fixed_spacing
    width = math.ceil((total_area / length) / fixed_spacing) * fixed_spacing

    # 縦と横の数を計算
    trees_along_length = int(length // fixed_spacing) + 1
    trees_along_width = int(width // fixed_spacing) + 1
    total_trees_count = trees_along_length * trees_along_width  # 柱の総本数

    # 柱の総面積を計算し、切り上げ
    hashira_area = math.ceil(total_trees_count * area_per_pillar)
    return hashira_area


# --- 結果の表示 ---
# 透析部門合計面積の計算
total = math.ceil(bed_area + machineroom_size + warehouse_size + stuffstation_area + warehouse_size2 + obutu + stuff_hos + hosupital_area + resutroom + kouisitu) 

# 柱の面積を計算（ここで関数を呼び出す）
hashira = calculate_pillar_area_fixed_spacing(total)


if month_patients:
    st.markdown("---")
    st.subheader("計算結果概要")
    st.write('**透析部門室面積合計:** ', f'{total} m²')
    st.write('**一日あたりの患者数想定:** ', f'{month_patients} 人')
    st.write('**ベッド数:** ', f'{day_patients} 台')
    st.write('**日勤スタッフ数想定:** ', f'{math.ceil(num_stuff)} 人')

# --- データフレーム ---
data = {
    "諸室名": ["透析室(ベッド廻り)", "スタッフステーション", "透析機械室", "機械室内物置", "汚物処理室", "器材庫面積", "便所", "スタッフ休憩室", "患者更衣室", "透析後患者休憩エリア", "柱・PS等", "その他","診察室・相談室",],
    "面積": [bed_area, stuffstation_area, machineroom_size, warehouse_size, obutu, warehouse_size2, resutroom, stuff_hos, kouisitu, hosupital_area, hashira, 0, 0,],
    "計算の仕方": [
        "ベッド廻りとベッド間通路の面積。個室一つにつき＋2㎡",
        "スタッフ数換算。形式により調整。体重計置場もココで換算している。",
        "ベッド数から計算。機械寸法、台数は別紙参照",
        "機械室の大きさから計算",
        "流し台＋SK。流し台個数により調整",
        "患者数から算出。車いすや歩行器等機器もココで見ている",
        "多目的便所サイズ",
        "スタッフ数より算出。人数による広さは別紙参照",
        "患者数より計算。外来患者が少ない場合は縮小。",
        "患者数より算出。病棟リハが主患者層の場合は無くせないか協議。",
        "柱やPSの面積（間隔７ⅿ程度）。階段やEVが必要な際は追加ください",
        "ベッド搬送が多い病院はベッド置場等を追加",
        "診察は外来で行う。"
    ],
}
df = pd.DataFrame(data)

# 小数点以下は切り上げ
df["面積"] = np.ceil(df["面積"]).astype(int)

# 諸室一覧表の表示
st.markdown("---")
st.subheader("算定諸室一覧 (面積を直接編集できます)")

# データフレーム編集
edited_df = st.data_editor(
    df,
    hide_index=True,
    column_config={
        "計算の仕方": st.column_config.TextColumn(
            width="290" # 列の幅を調整
        )
    }
)

# 編集された面積の合計を再計算して表示
if edited_df is not None:
    updated_total = edited_df["面積"].sum()
    st.write(f"**柱追加、その他編集後の合計面積:** {updated_total} m²")

st.write("近年の透析部門は１ベッドあたり約15～25㎡です")
st.write(f"{day_patients}ベッドでは約{day_patients*15}～{day_patients*25}㎡です")

tousekisitu = math.ceil(bed_area + stuffstation_area)
st.write(f"**透析室面積（ベッド廻り＋スタッフステーション）:** {tousekisitu}㎡")
st.write("透析室は１ベッドあたり約8～12㎡です。")
st.write(f"{day_patients}ベッドでは約{day_patients*8}～{day_patients*12}㎡です")

# 参考図の表示
st.markdown("---")
st.write(f"**透析室面積算定参考（ベッド廻り）**")
pdf_viewer(r"C:\Users\d_hin\Desktop\touseki\01.pdf")