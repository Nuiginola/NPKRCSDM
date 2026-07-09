"""
NPK RC SDM — โปรแกรมออกแบบคอนกรีตเสริมเหล็กโดยวิธีกำลัง (Strength Design Method)
งานวิจัยระดับปริญญาโท | ขอบเขต: อาคารบ้านพักอาศัย
กฎกระทรวง กำหนดการออกแบบโครงสร้างอาคารฯ พ.ศ. 2566

หน้าแรก / เมนูหลักของโปรแกรม — ใช้ st.navigation()/st.Page() (ไม่ใช่ pages/ folder
แบบ auto-discovery แบบเดิม) เพราะ st.page_link() แบบอ้างอิงด้วย string path ไปยัง
ไฟล์ที่มีชื่อภาษาไทย เจอบั๊ก KeyError('url_pathname') บนเครื่อง Windows ของผู้ใช้
การอ้างอิงด้วย st.Page object โดยตรงไม่มีปัญหานี้ และคุมชื่อเมนู (Thai label) ผ่าน
พารามิเตอร์ title=/label= ได้ตรงๆ โดยไม่ต้องพึ่งชื่อไฟล์ภาษาไทย

Entry point (Streamlit). Run with: streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="NPK RC SDM", layout="wide")


def home():
    st.title("NPK RC SDM")
    st.caption("โปรแกรมออกแบบคอนกรีตเสริมเหล็กโดยวิธีกำลัง (SDM) ตามกฎกระทรวง "
               "กำหนดการออกแบบโครงสร้างอาคารฯ พ.ศ. 2566")
    st.divider()

    with st.container(border=True):
        st.subheader("📁 ข้อมูลโครงการ")
        st.page_link(project_info_page, label="เปิดหน้าข้อมูลโครงการ", icon="📁")

    st.write("")

    with st.container(border=True):
        st.subheader("⚙️ พารามิเตอร์การออกแบบ")
        st.page_link(design_params_page, label="เปิดหน้าพารามิเตอร์การออกแบบ", icon="⚙️")

    st.write("")

    with st.container(border=True):
        st.subheader("1. พื้น (Slab)")
        st.page_link(slab_on_ground_page, label="1.1 พื้นวางบนดิน (Slab on Ground)", icon="✅")
        st.page_link(one_way_slab_page, label="1.2 พื้นทางเดียว (One-way Slab)", icon="✅")
        st.page_link(two_way_slab_page, label="1.3 พื้นสองทาง (Two-way Slab)", icon="✅")
        st.page_link(cantilever_slab_page, label="1.4 พื้นยื่น (Cantilever Slab)", icon="✅")

    st.write("")

    with st.container(border=True):
        st.subheader("2. บันได (Stair)")
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;2.1 บันไดช่วงตรง (Straight Stair) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;2.2 บันไดหักกลับ (U Shape Stair) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.subheader("3. คาน (Beam)")
        st.page_link(beam_single_span_page, label="3.1 คานช่วงเดียว (Single-span Beam)", icon="✅")
        st.page_link(continuous_beam_page, label="3.2 คานต่อเนื่อง (Continuous Beam)", icon="✅")
        st.page_link(cantilever_beam_page, label="3.3 คานยื่น (Cantilever Beam)", icon="✅")

    st.write("")

    with st.container(border=True):
        st.subheader("4. เสา (Column)")
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;4.1 เสาสี่เหลี่ยม — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;4.2 เสากลม — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.subheader("5. ฐานราก (Footing)")
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;5.1 ฐานรากแผ่ (Spread Footing) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;5.2 ฐานเสาเข็ม 2 ต้น (Pile Cap) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;5.3 ฐานเสาเข็ม 3 ต้น (Pile Cap) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;5.4 ฐานเสาเข็ม 4 ต้น (Pile Cap) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;5.5 ฐานเสาเข็ม 5 ต้น (Pile Cap) — *ยังไม่เปิดใช้งาน*", unsafe_allow_html=True)


home_page = st.Page(home, title="หน้าแรก", icon="🏠", default=True)
project_info_page = st.Page("app_pages/project_info.py", title="ข้อมูลโครงการ", icon="📁")
design_params_page = st.Page("app_pages/design_parameters.py", title="พารามิเตอร์การออกแบบ", icon="⚙️")
slab_on_ground_page = st.Page("app_pages/slab_on_ground.py", title="1.1 พื้นวางบนดิน", icon="✅")
one_way_slab_page = st.Page("app_pages/one_way_slab.py", title="1.2 พื้นทางเดียว", icon="✅")
two_way_slab_page = st.Page("app_pages/two_way_slab.py", title="1.3 พื้นสองทาง", icon="✅")
cantilever_slab_page = st.Page("app_pages/cantilever_slab.py", title="1.4 พื้นยื่น", icon="✅")
beam_single_span_page = st.Page("app_pages/beam_single_span.py", title="3.1 คานช่วงเดียว", icon="✅")
continuous_beam_page = st.Page("app_pages/continuous_beam.py", title="3.2 คานต่อเนื่อง", icon="✅")
cantilever_beam_page = st.Page("app_pages/cantilever_beam.py", title="3.3 คานยื่น", icon="✅")

pg = st.navigation([home_page, project_info_page, design_params_page, slab_on_ground_page,
                     one_way_slab_page, two_way_slab_page, cantilever_slab_page,
                     beam_single_span_page, continuous_beam_page, cantilever_beam_page])
pg.run()
