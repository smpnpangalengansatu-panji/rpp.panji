import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="AI RPP Generator Expert", 
    page_icon="🎓",
    layout="wide"
)

# --- TAMBAHAN FITUR: CUSTOM CSS UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    /* Mengubah font ke Inter/Sans Serif yang lebih modern */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Warna Background Utama */
    .main {
        background-color: #f4f7f9;
    }

    /* Styling Card/Kontainer Input */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: none;
    }

    /* Styling Tombol */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #007bff;
        color: white;
        font-weight: 600;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 12px rgba(0,123,255,0.3);
    }

    /* Styling Input Field */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }

    /* Header Styling */
    h1, h2, h3 {
        color: #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI PARSER UNTUK MERAPIKAN DOCX (TETAP SAMA) ---
def create_formatted_docx(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    lines = text.split('\n')
    is_table = False
    table_data = []

    for line in lines:
        clean_line = line.strip()
        if '|' in clean_line:
            if '---' in clean_line: continue
            cells = [c.strip() for c in clean_line.split('|') if c.strip()]
            if cells:
                table_data.append(cells)
                is_table = True
            continue
        else:
            if is_table and table_data:
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                table.style = 'Table Grid'
                for i, row in enumerate(table_data):
                    for j, cell_text in enumerate(row):
                        table.rows[i].cells[j].text = cell_text.replace('**', '')
                table_data = []
                is_table = False
                doc.add_paragraph()
        if not clean_line: continue
        if clean_line.startswith('#'):
            level = clean_line.count('#')
            doc.add_heading(clean_line.replace('#', '').strip(), level=min(level, 3))
        elif clean_line.startswith(('* ', '- ')):
            doc.add_paragraph(clean_line[2:].replace('**', ''), style='List Bullet')
        elif clean_line[0:1].isdigit() and clean_line[1:2] == '.':
            doc.add_paragraph(clean_line[2:].strip().replace('**', ''), style='List Number')
        elif clean_line.startswith('**') and clean_line.endswith('**'):
            p = doc.add_paragraph()
            run = p.add_run(clean_line.replace('**', ''))
            run.bold = True
        else:
            doc.add_paragraph(clean_line.replace('**', ''))
    return doc

# --- TAMBAHAN FITUR: SIDEBAR UNTUK INFO PENGGUNA ---
with st.sidebar:
    st.markdown("### 🎓 Admin Kurikulum AI")
    st.image("https://cdn-icons-png.flaticon.com/512/3976/3976625.png", width=100)
    st.info("Aplikasi ini membantu Guru menyusun Modul Ajar Kurikulum Merdeka secara otomatis dengan standar terbaru.")
    st.divider()
    st.caption("v2.1 - Professional Edition")

# --- INISIALISASI SESSION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'data' not in st.session_state:
    st.session_state.data = {}

def go_to_page(page_number):
    st.session_state.page = page_number
    st.rerun()

# --- HALAMAN 1: INPUT DATA DASAR ---
if st.session_state.page == 1:
    st.title("📝 Penyusunan Modul Ajar")
    st.subheader("Bagian 1: Data Isian Dasar")
    
    with st.form("form_halaman_1"):
        st.markdown("#### 🔑 Konfigurasi API")
        api_key = st.text_input("Masukkan API Key Gemini Anda:", type="password", help="Dapatkan di Google AI Studio")
        
        st.markdown("#### 👤 Identitas Guru & Sekolah")
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Guru", placeholder="Contoh: Budi Santoso, S.Pd")
            unit = st.text_input("Unit Kerja (Sekolah)", placeholder="Contoh: SMA Negeri 1 Jakarta")
            mapel = st.text_input("Mata Pelajaran")
            fase = st.selectbox("Fase", ["A", "B", "C", "D", "E", "F"])
        
        with col2:
            kelas = st.text_input("Kelas")
            semester = st.selectbox("Semester", ["1 (Ganjil)", "2 (Genap)"])
            jp = st.text_input("Alokasi Waktu", placeholder="Contoh: 2 x 45 Menit")
            topik = st.text_input("Topik / Tema Pembelajaran")

        st.markdown("#### ⚙️ Pengaturan Model")
        model_belajar = st.selectbox("Model Pembelajaran", [
            "Pembelajaran Berbasis Masalah (PBL)", 
            "Pembelajaran Berbasis Proyek (PjBL)", 
            "Inquiry Learning", 
            "Discovery Learning", 
            "Contextual Teaching and Learning (CTL)"
        ])
        pertemuan = st.number_input("Jumlah Pertemuan", min_value=1, value=1)

        st.markdown("<br>", unsafe_allow_html=True)
        submit_1 = st.form_submit_button("Lanjut ke Konfirmasi →")
        
        if submit_1:
            if not api_key or not nama or not topik:
                st.error("Mohon lengkapi data wajib (API Key, Nama, dan Topik)!")
            else:
                st.session_state.data = {
                    'api_key': api_key, 'nama': nama, 'unit': unit, 'mapel': mapel,
                    'fase': fase, 'kelas': kelas, 'semester': semester,
                    'jp': jp, 'pertemuan': pertemuan, 'topik': topik, 'model': model_belajar
                }
                go_to_page(2)

# --- HALAMAN 2: KONFIRMASI DATA ---
elif st.session_state.page == 2:
    st.title("🔍 Konfirmasi Data")
    st.success("Data berhasil disimpan! Mohon tinjau kembali sebelum diproses oleh AI.")
    
    d = st.session_state.data
    
    # Menampilkan data dalam kolom yang rapi (Bukan input field agar terlihat seperti ringkasan)
    with st.container():
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Nama Guru:** {d['nama']}")
            st.write(f"**Sekolah:** {d['unit']}")
            st.write(f"**Mata Pelajaran:** {d['mapel']}")
            st.write(f"**Topik:** {d['topik']}")
        with c2:
            st.write(f"**Fase/Kelas:** {d['fase']} / {d['kelas']}")
            st.write(f"**Model:** {d['model']}")
            st.write(f"**Alokasi:** {d['jp']} ({d['pertemuan']} Pertemuan)")
        st.markdown("---")

    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("⬅️ Kembali & Perbaiki"):
            go_to_page(1)
    with col_nav2:
        if st.button("🚀 Generate RPP Sekarang"):
            go_to_page(3)

# --- HALAMAN 3: GENERATE ---
elif st.session_state.page == 3:
    st.title("✨ Hasil Modul Ajar AI")
    d = st.session_state.data
    
    try:
        genai.configure(api_key=d['api_key'])
        
        with st.spinner("Mencari model terbaik untuk Anda..."):
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in all_models if "gemini-1.5-flash" in m), all_models[0])

        model = genai.GenerativeModel(target_model)
        
        # PROMPT ENGINEERING SESUAI SINTAK USER
        prompt = f"""
        Bertindaklah sebagai Guru Ahli Kurikulum Merdeka. Buatlah RPP lengkap dengan struktur:
        
        IDENTITAS: Nama: {d['nama']}, Unit: {d['unit']}, Mapel: {d['mapel']}, Fase/Kelas/Sem: {d['fase']}/{d['kelas']}/{d['semester']}, Alokasi: {d['jp']}, Pertemuan: {d['pertemuan']}, Topik: {d['topik']}.

        A. CAPAIAN PEMBELAJARAN PER-ELEMEN: (Rumusan elemen & CP berdasarkan topik {d['topik']}).
        B. DIMENSI PROFIL LULUSAN (DPL): (Pilih & jelaskan yang relevan dari 8 dimensi: Keimanan, Kewargaan, Penalaran Kritis, Kreatifitas, Kolaborasi, Kemandirian, Kesehatan, Komunikasi).
        C. RUANG LINGKUP MATERI: (Tuliskan secara sistematis).
        D. DESIGN PEMBELAJARAN:
           1. TUJUAN PEMBELAJARAN: (Wajib mengandung unsur ABCD: Audience, Behavior, Condition, Degree).
           2. PRAKTIK PAEDAGOGIS: (Gunakan model {d['model']} dengan sintak lengkap).
           3. KEMITRAAN (Opsional). 4. LINGKUNGAN BELAJAR. 5. PEMANFAATAN DIGITAL (Opsional).
        E. LANGKAH-LANGKAH PEMBELAJARAN:
           (Rinci kegiatan Guru & Siswa. Integrasikan SINTAK {d['model']} ke dalam 3 kategori:
           1. MEMAHAMI (Berkesadaran & Bermakna)
           2. MENGAPLIKASI (Berkesadaran, Bermakna, Menyenangkan)
           3. MEREFLEKSI (Berkesadaran & Bermakna))
           - Buat dalam sub-bagian: a. Pendahuluan, b. Inti, c. Penutup.
        F. ASESMEN: (Buat Tabel Instrumen & Tabel Teknik (Tes/Non-Tes) lengkap dengan soal, jawaban, dan rubrik).
        G. MEDIA, ALAT, DAN SUMBER: (Sumber belajar format: Penulis, Tahun, Judul, Hal, Kota).
        H. CATATAN & I. RINGKASAN MATERI (Pengertian, fungsi, contoh soal & penjelasan).
        LAMPIRAN: LKPD Interaktif dan Rubriknya.
        """

        # Gunakan container untuk hasil agar terlihat rapi
        with st.status("AI sedang bekerja keras menyusun RPP...", expanded=True) as status:
            st.write("Menganalisis Topik...")
            response = model.generate_content(prompt)
            st.write("Menyusun Struktur Kurikulum...")
            status.update(label="RPP Selesai Dibuat!", state="complete", expanded=False)

        st.markdown(response.text)
        
        doc = create_formatted_docx(response.text, f"RPP - {d['topik']}")
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        st.divider()
        c_dl, c_new = st.columns([3, 1])
        with c_dl:
            st.download_button(
                label="📥 Download Dokumen Modul Ajar (.docx)",
                data=buffer,
                file_name=f"RPP_{d['topik'].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with c_new:
            if st.button("➕ Buat Baru", use_container_width=True):
                go_to_page(1)

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
        if st.button("Coba Lagi"):
            go_to_page(1)