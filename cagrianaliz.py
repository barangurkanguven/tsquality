import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Tedarik Sürekliliği Veri Kalite Plaftormu")

# -------------------------
# BÖLÜM 1: ARDIŞIK KESİNTİLERDE ÇAĞRI KAYDI OLANLAR
# -------------------------
st.header("1. Ardışık Kesintilerde Aynı Kullanıcının Çağrı Kaydı Bıraktığı Kesintiler")

max_saat = st.number_input(
    "🔧 Kaç saate kadar ardışıklık kontrol edilsin? (min: 1 saniye ≈ 0.00028, max: 240 saat)",
    min_value=0.00028, max_value=240.0, value=10.0, step=0.1, key="b1"
)

file1 = st.file_uploader("📄 Cagri_List.xlsx dosyasını yükleyin", type=["xlsx"], key="f1")
if file1:
    df1 = pd.read_excel(file1, engine="openpyxl", header=2)
    df1.columns = df1.columns.str.strip()
    df1["KESINTI BASLANGIC SAATI"] = pd.to_datetime(df1["KESINTI BASLANGIC SAATI"], dayfirst=True, errors="coerce")
    df1["KESINTI BITIS SAATI"] = pd.to_datetime(df1["KESINTI BITIS SAATI"], dayfirst=True, errors="coerce")

    ardışık_kayitlar = []
    for musteri, grup in df1.groupby("MUSTERI"):
        grup = grup.sort_values("KESINTI BASLANGIC SAATI").reset_index(drop=True)
        zincir = [grup.loc[0]]
        for i in range(1, len(grup)):
            onceki = zincir[-1]
            simdiki = grup.loc[i]
            fark = (simdiki["KESINTI BASLANGIC SAATI"] - onceki["KESINTI BITIS SAATI"]).total_seconds() / 3600
            if 0 < fark <= max_saat:
                zincir.append(simdiki)
            else:
                if len(zincir) > 1:
                    satir = {"MUSTERI": musteri}
                    b1, b2 = zincir[0]["KESINTI BASLANGIC SAATI"], zincir[-1]["KESINTI BITIS SAATI"]
                    sure = (b2 - b1).total_seconds() / 3600
                    for j, z in enumerate(zincir):
                        satir[f"#{j+1} KOD"] = z["KESINTI_KOD"]
                        satir[f"#{j+1} Ş.UNSU"] = z["SEBEKE UNSURU"]
                        satir[f"#{j+1} BAŞ"] = z["KESINTI BASLANGIC SAATI"]
                        satir[f"#{j+1} BİT"] = z["KESINTI BITIS SAATI"]
                    satir["BİRLEŞİRSE SÜRE (saat)"] = round(sure, 2)
                    ardışık_kayitlar.append(satir)
                zincir = [simdiki]
        if len(zincir) > 1:
            satir = {"MUSTERI": musteri}
            b1, b2 = zincir[0]["KESINTI BASLANGIC SAATI"], zincir[-1]["KESINTI BITIS SAATI"]
            sure = (b2 - b1).total_seconds() / 3600
            for j, z in enumerate(zincir):
                satir[f"#{j+1} KOD"] = z["KESINTI_KOD"]
                satir[f"#{j+1} Ş.UNSU"] = z["SEBEKE UNSURU"]
                satir[f"#{j+1} BAŞ"] = z["KESINTI BASLANGIC SAATI"]
                satir[f"#{j+1} BİT"] = z["KESINTI BITIS SAATI"]
            satir["BİRLEŞİRSE SÜRE (saat)"] = round(sure, 2)
            ardışık_kayitlar.append(satir)
    if ardışık_kayitlar:
        st.success("✅ Ardışık çağrılı kesintiler bulundu.")
        st.dataframe(pd.DataFrame(ardışık_kayitlar))
    else:
        st.info("Bu kriterlerde ardışık çağrı bulunamadı.")

# -------------------------
# BÖLÜM 2: MÜKERRER GRUPLAMA + KARAR + YENİ SÜRE
# -------------------------
st.markdown("---")
st.header("2. Mükerrer Kesinti Kontrolü (Gruplama + Karar + Süre)")

file2 = st.file_uploader("📄 Kesinti_List.xlsx dosyasını yükleyin", type=["xlsx"], key="f2")
if file2:
    df2 = pd.read_excel(file2, engine="openpyxl", header=2)
    df2.columns = df2.columns.str.strip()
    df2["KESINTI BASLANGIC SAATI"] = pd.to_datetime(df2["KESINTI BASLANGIC SAATI"], dayfirst=True, errors="coerce")
    df2["KESINTI BITIS SAATI"] = pd.to_datetime(df2["KESINTI BITIS SAATI"], dayfirst=True, errors="coerce")

    df2.sort_values(by=["SEBEKE UNSURU", "KESINTI BASLANGIC SAATI"], inplace=True)
    df2.reset_index(drop=True, inplace=True)

    results = []
    grup_sayac = 1

    for unsur, grup in df2.groupby("SEBEKE UNSURU"):
        grup = grup.sort_values("KESINTI BASLANGIC SAATI").reset_index(drop=True)
        zincir = []
        grup_id = f"GRUP_{grup_sayac:03d}"
        for i in range(len(grup)):
            k = grup.loc[i]
            if not zincir:
                zincir.append(k)
            else:
                if k["KESINTI BASLANGIC SAATI"] <= zincir[-1]["KESINTI BITIS SAATI"]:
                    zincir.append(k)
                else:
                    if len(zincir) > 1:
                        gb, ge = zincir[0]["KESINTI BASLANGIC SAATI"], zincir[-1]["KESINTI BITIS SAATI"]
                        sure = (ge - gb).total_seconds() / 3600
                        for j, z in enumerate(zincir):
                            karar = "MEVCUT" if j == 0 else "İPTAL"
                            results.append({
                                "GRUP ID": grup_id,
                                "SEBEKE UNSURU": unsur,
                                "KESINTI_KOD": z["KESINTI_KOD"],
                                "KESINTI BAŞ": z["KESINTI BASLANGIC SAATI"],
                                "KESINTI BİT": z["KESINTI BITIS SAATI"],
                                "GRUP BAŞ": gb,
                                "GRUP BİT": ge,
                                "KARAR": karar,
                                "YENİ SÜRE (saat)": round(sure, 2) if karar == "MEVCUT" else None
                            })
                        grup_sayac += 1
                    zincir = [k]
        if len(zincir) > 1:
            gb, ge = zincir[0]["KESINTI BASLANGIC SAATI"], zincir[-1]["KESINTI BITIS SAATI"]
            sure = (ge - gb).total_seconds() / 3600
            for j, z in enumerate(zincir):
                karar = "MEVCUT" if j == 0 else "İPTAL"
                results.append({
                    "GRUP ID": grup_id,
                    "SEBEKE UNSURU": unsur,
                    "KESINTI_KOD": z["KESINTI_KOD"],
                    "KESINTI BAŞ": z["KESINTI BASLANGIC SAATI"],
                    "KESINTI BİT": z["KESINTI BITIS SAATI"],
                    "GRUP BAŞ": gb,
                    "GRUP BİT": ge,
                    "KARAR": karar,
                    "YENİ SÜRE (saat)": round(sure, 2) if karar == "MEVCUT" else None
                })
            grup_sayac += 1
    if results:
        st.success("✅ Mükerrer gruplar oluşturuldu ve kararlar belirlendi.")
        st.dataframe(pd.DataFrame(results))
    else:
        st.info("Zaman çakışması içeren kesinti grubu bulunamadı.")

# -------------------------
# BÖLÜM 3: ARDIŞIK KESİNTİLER (ÇAĞRISIZ, MÜKERRER OLMAYAN)
# -------------------------
st.markdown("---")
st.header("3. Ardışık Kesinti Tespiti (Ardışıklık Saati Kullanıcı Tarafından Belirlenir)")

st.warning("Not:Bu analizi şebeke unsuru bazında zamansal kesişme durumlarını ortadan kaldırdıktan sonra çalıştırınız.")

max_gap = st.number_input(
    "⏱ Kaç saate kadar ardışık kesintiler kontrol edilsin?", min_value=0.00028, max_value=240.0, value=4.0, step=0.1, key="b3"
)

file3 = st.file_uploader("📄 Kesinti_List.xlsx dosyasını yükleyin", type=["xlsx"], key="f3")
if file3:
    df3 = pd.read_excel(file3, engine="openpyxl", header=2)
    df3.columns = df3.columns.str.strip()
    df3["KESINTI BASLANGIC SAATI"] = pd.to_datetime(df3["KESINTI BASLANGIC SAATI"], dayfirst=True, errors="coerce")
    df3["KESINTI BITIS SAATI"] = pd.to_datetime(df3["KESINTI BITIS SAATI"], dayfirst=True, errors="coerce")

    df3.sort_values(by=["SEBEKE UNSURU", "KESINTI BASLANGIC SAATI"], inplace=True)
    gruplu_sonuclar = []
    grup_sayac = 1

    for unsur, grup in df3.groupby("SEBEKE UNSURU"):
        grup = grup.sort_values("KESINTI BASLANGIC SAATI").reset_index(drop=True)
        zincir = [grup.loc[0]]

        for i in range(1, len(grup)):
            onceki = zincir[-1]
            simdiki = grup.loc[i]
            fark = (simdiki["KESINTI BASLANGIC SAATI"] - onceki["KESINTI BITIS SAATI"]).total_seconds() / 3600
            if 0 < fark <= max_gap:
                zincir.append(simdiki)
            else:
                if len(zincir) > 1:
                    grup_id = f"GRUP_{grup_sayac:03d}"
                    yeni_bit = zincir[-1]["KESINTI BITIS SAATI"]
                    yeni_sure = (yeni_bit - zincir[0]["KESINTI BASLANGIC SAATI"]).total_seconds() / 3600
                    for j, z in enumerate(zincir):
                        gruplu_sonuclar.append({
                            "GRUP ID": grup_id,
                            "SEBEKE UNSURU": unsur,
                            "KESINTI_KOD": z["KESINTI_KOD"],
                            "MEVCUT BAŞLANGIÇ": z["KESINTI BASLANGIC SAATI"],
                            "MEVCUT BİTİŞ": z["KESINTI BITIS SAATI"],
                            "KARAR": "MEVCUT" if j == 0 else "İPTAL",
                            "YENİ BİTİŞ (sadece MEVCUT için)": yeni_bit if j == 0 else None,
                            "YENİ SÜRE (saat)": round(yeni_sure, 2) if j == 0 else None
                        })
                    grup_sayac += 1
                zincir = [simdiki]

        if len(zincir) > 1:
            grup_id = f"GRUP_{grup_sayac:03d}"
            yeni_bit = zincir[-1]["KESINTI BITIS SAATI"]
            yeni_sure = (yeni_bit - zincir[0]["KESINTI BASLANGIC SAATI"]).total_seconds() / 3600
            for j, z in enumerate(zincir):
                gruplu_sonuclar.append({
                    "GRUP ID": grup_id,
                    "SEBEKE UNSURU": unsur,
                    "KESINTI_KOD": z["KESINTI_KOD"],
                    "ORJ. BAŞLANGIÇ": z["KESINTI BASLANGIC SAATI"],
                    "ORJ. BİTİŞ": z["KESINTI BITIS SAATI"],
                    "KARAR": "MEVCUT" if j == 0 else "İPTAL",
                    "YENİ BİTİŞ (sadece MEVCUT için)": yeni_bit if j == 0 else None,
                    "YENİ SÜRE (saat)": round(yeni_sure, 2) if j == 0 else None
                })
            grup_sayac += 1

    if gruplu_sonuclar:
        st.success("🔁 Ardışık ama çakışmayan kesintiler gruplanarak mevcut/iptal ayrımı yapıldı.")
        st.dataframe(pd.DataFrame(gruplu_sonuclar))
    else:
        st.info("Belirtilen ardışıklık süresi içerisinde ardışık kesinti zinciri bulunamadı.")

