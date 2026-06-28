#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 00_raw_data_inspection.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
# =============================================================================
from pathlib import Path
from datetime import datetime

path = Path(r"E:\project_flood_impact_assessment\census\spss_2015.dta")

# Original notebook comment normalized for the public code archive.
st = path.stat()
def human(n):
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.0f} PB"

print("[INFO] Notebook progress message.", path)
print("[INFO] Notebook progress message.", human(st.st_size))
print("[INFO] Notebook progress message.", datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))

# Original notebook comment normalized for the public code archive.
try:
    import pyreadstat
    # Original notebook comment normalized for the public code archive.
    _, meta = pyreadstat.read_dta(str(path), row_limit=0)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.", getattr(meta, "file_format_version", "[INFO] Notebook progress message."))
    print("[INFO] Notebook progress message.", getattr(meta, "number_rows", "[INFO] Notebook progress message."))
    print("[INFO] Notebook progress message.", getattr(meta, "number_columns", "[INFO] Notebook progress message."))
    print("[INFO] Notebook progress message.", getattr(meta, "file_label", ""))

    cols = list(meta.column_names)
    print("[INFO] Notebook progress message.", cols[:20])

    # Original notebook comment normalized for the public code archive.
    labels = list(meta.column_labels or [])
    has_any_labels = any(bool(x) for x in labels)
    if has_any_labels:
        print("[INFO] Notebook progress message.")
        shown = 0
        for i, name in enumerate(cols[:20]):
            lab = (labels[i] or "").strip()
            if lab:
                print(f"  - {name}: {lab}")
                shown += 1
        if shown == 0:
            print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    v2l = getattr(meta, "variable_to_label", None)
    vls = getattr(meta, "value_labels", None)
    if v2l and vls:
        print("[INFO] Notebook progress message.")
        shown = 0
        for var, labelset in v2l.items():
            if labelset in vls:
                items = list(vls[labelset].items())[:5]
                print(f"  - {var} ({labelset}): {items}")
                shown += 1
                if shown >= 3:
                    break

    # Original notebook comment normalized for the public code archive.
    df_head, _ = pyreadstat.read_dta(str(path), row_limit=5)
    print("[INFO] Notebook progress message.")
    display(df_head)
    print("[INFO] Notebook progress message.")
    print(df_head.dtypes[:20])

except ModuleNotFoundError:
    import pandas as pd
    print("[INFO] Notebook progress message.")
    with pd.read_stata(path, iterator=True, chunksize=5, convert_categoricals=False) as rdr:
        head = rdr.read(5)
    print("[INFO] Notebook progress message.", head.shape[1])
    print("[INFO] Notebook progress message.", list(head.columns[:20]))
    display(head)


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
import pandas as pd
path = r"E:\project_flood_impact_assessment\census\spss_2015.dta"

# Original notebook comment normalized for the public code archive.
df = pd.read_stata(path, convert_categoricals=False)

print("[INFO] Notebook progress message.", df.shape)
display(df.head())

# Original notebook comment normalized for the public code archive.
prof = (
    pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "non_null": df.notna().sum(),
        "missing_%": (df.isna().mean()*100).round(2),
        "n_unique": df.nunique(dropna=True),
    })
    .sort_index()
)
display(prof.head(20))  # Original notebook comment normalized for the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
import pyreadstat, pandas as pd

path = r"E:\project_flood_impact_assessment\census\spss_2015.dta"

df, meta = pyreadstat.read_dta(path)          # Original notebook comment normalized for the public code archive.
name2label = dict(zip(meta.column_names, meta.column_labels or []))

# Original notebook comment normalized for the public code archive.
list(name2label.items())[:20]

# Original notebook comment normalized for the public code archive.
var_dict = pd.DataFrame({
    "var": meta.column_names,
    "label": [lbl or "" for lbl in (meta.column_labels or [])],
})
display(var_dict.head(20))
var_dict.to_excel(r"E:\project_flood_impact_assessment\census\变量字典_2015.xlsx", index=False)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
print(meta.variable_to_label)        # Original notebook comment normalized for the public code archive.
print({k: list(v.items())[:10] for k,v in (meta.value_labels or {}).items()})  # Original notebook comment normalized for the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
import pyreadstat, pandas as pd, pathlib, json

# Original notebook comment normalized for the public code archive.
path = r"E:\project_flood_impact_assessment\census\spss_2015.dta"
df, meta = pyreadstat.read_dta(path)

# Original notebook comment normalized for the public code archive.
rows = []
for var in meta.column_names:
    labset = meta.variable_to_label.get(var)
    if labset and labset in meta.value_labels:
        for code, label in meta.value_labels[labset].items():
            rows.append({"var": var, "code": str(code), "label": str(label), "source": "from_dta"})

# Original notebook comment normalized for the public code archive.
from_docs = {
    "M7":  ["家庭户","集体户"],
    "M8":  ["普通住宅","集体宿舍和工棚","工作地住宿","无住房"],
    "M11": ["平房","2-3层楼房","4-6层楼房","7-9层楼房","10层以上楼房"],
    "M12": ["1949年以前","1949-1959年","1960-1969年","1970-1979年","1980-1989年","1990-1999年","2000-2009年","2010年以后"],
    "M13": ["独立使用","与其他户合用","无"],
    "M14": ["独立使用抽水/冲水式","合用抽水/冲水式","独立使用其他样式","合用其他样式","无"],
    "M15": ["购买新建商品房","购买二手房","购买原公有住房","购买经济适用房/两限房","自建住房","租赁廉租房/公租房","租赁其他住房","其他"],
    "M16": ["≥100万元","50-100万元","30-50万元","20-30万元","10-20万元","10万元以下"],
    "M33": ["户主","配偶","子女","父母","岳父母或公婆","祖父母/外祖父母/曾祖父母","媳婿","孙子女","兄弟姐妹","其他"],
    "M34": ["男","女"],
    "M42": ["不满半年","半年至一年","一至二年","二至三年","三至四年","四至五年","五至十年","十年以上"],
    "M43": ["没有离开户口登记地","不满半年","半年至一年","一至二年","二至三年","三至四年","四至五年","五至十年","十年以上"],
    "M44": ["工作就业","学习培训","随同迁移","房屋拆迁","改善住房","寄挂户口","婚姻嫁娶","为子女就学","其他"],
    "M45": ["有","无"],
    "M50": ["是","否"],
    "M51": ["未上过学","小学","初中","普通高中","中职","大学专科","大学本科","研究生"],
    "M52": ["在校","毕业","肄业","辍学","其他"],
    "M53": ["在工作","在职休假/在职学习培训/临时停工或季节性歇业","未做任何工作"],
    "M59_loc": ["现住房所在的街道(乡/镇)","本市其他街道(乡/镇)","本市以外"],  # Original notebook comment normalized for the public code archive.
    "M59_ring": ["二环以内","二环至三环","三环至四环","四环至五环","五环至六环","六环以外"],   # Original notebook comment normalized for the public code archive.
    "M61": ["步行","自行车","电动车","摩托车","小轿车","公共汽车","轨道交通","其他"],
    "M63": ["在校学习","丧失工作能力","毕业后未工作","因单位原因失去工作","因本人原因失去工作","承包土地被征用","离退休","料理家务","其他"],
    "M64": ["在职业介绍机构求职","委托亲友找工作","应答或刊登广告","参加招聘会","为自己经营作准备","其他","未找过工作"],
    "M65": ["能","不能"],
    "M66": ["城镇职工基本养老保险","城镇(乡)居民社会养老保险","新型农村社会养老保险","机关事业单位养老保险","未参加以上四种社会养老保险"],
    "M67": ["职工基本医疗保险","城镇(乡)居民基本医疗保险","新型农村合作医疗","公费医疗","未参加以上四种基本医疗保险"],
    "M68": ["未婚","有配偶","离婚","丧偶"],
    "M69": ["双独","单独,女方为独生子女","单独,男方为独生子女","均非独生子女"],
    "M70": ["未生育","有生育"],
    "M75": ["未生育","有生育"],
    "M77": ["男","女"],
    "M82": ["劳动收入","离退休金养老金","最低生活保障金","财产性收入","家庭其他成员供养","其他"],
    "M83": ["健康","基本健康","不健康,但生活能自理","生活不能自理"],
}

for var, opts in from_docs.items():
    if var not in meta.variable_to_label:  # Original notebook comment normalized for the public code archive.
        for i, text in enumerate(opts, 1):
            rows.append({"var": var, "code": str(i), "label": text, "source": "from_docs"})

codebook = pd.DataFrame(rows).sort_values(["var", "code"])
outfile = pathlib.Path(path).with_name("变量取值编码_2015.xlsx")
codebook.to_excel(outfile, index=False)
print("[INFO] Notebook progress message.")
