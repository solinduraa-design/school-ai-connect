import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse

# 1. إعداد الصفحة
st.set_page_config(page_title="المساعد المدرسي الذكي", page_icon="🎓")

st.title("🎓 مساعد التواصل مع أولياء الأمور")
st.write("ارفع تقرير الطالب، وسأقوم بتحليله وتجهيز رسالة واتساب لولي الأمر.")

# 2. إعداد مفتاح الذكاء الاصطناعي من إعدادات الموقع السرية
# سنقوم بضبط هذا لاحقاً في خطوة الاستضافة
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("مفتاح الذكاء الاصطناعي غير موجود. يرجى إضافته في Secrets.")

# 3. تحميل قاعدة بيانات أولياء الأمور
try:
    parents_df = pd.read_csv("parents_data.csv")
    st.sidebar.success("تم تحميل بيانات أولياء الأمور بنجاح ✅")
except:
    st.sidebar.error("لم يتم العثور على ملف parents_data.csv")

# 4. مكان رفع صورة التقرير
uploaded_file = st.file_uploader("ارفع صورة تقرير الطالب (أو التقط صورة)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # عرض الصورة
    image = Image.open(uploaded_file)
    st.image(image, caption='التقرير المرفوع', use_column_width=True)
    
    # زر التحليل
    if st.button("تحليل التقرير وإنشاء الرسالة 🤖"):
        with st.spinner('جاري قراءة التقرير والتفكير...'):
            try:
                # تجهيز الموديل
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # الأمر (Prompt)
                prompt = """
                أنت مساعد تربوي ذكي. قم بتحليل صورة تقرير الطالب المرفقة.
                1. استخرج اسم الطالب.
                2. استخرج المادة أو الموضوع الذي درسه.
                3. اكتب رسالة واتساب قصيرة جداً وودودة باللهجة المصرية (أو العربية البسيطة) لولي الأمر.
                4. الرسالة يجب أن تحتوي على: ترحيب، ماذا تعلم الطالب، وسؤال ممتع للنقاش على العشاء، ونصيحة بسيطة.
                5. اجعل المخرجات بهذا الشكل الدقيق:
                Name: [اسم الطالب]
                Message: [نص الرسالة]
                """
                
                # إرسال للصورة لجمناي
                response = model.generate_content([prompt, image])
                result_text = response.text
                
                # استخراج البيانات من النص
                st.subheader("النتيجة:")
                st.text(result_text) # عرض النتيجة الخام للتأكد
                
                # محاولة استخراج الاسم والرسالة بشكل منفصل (بسيط)
                student_name = ""
                message_body = ""
                
                lines = result_text.split('\n')
                for line in lines:
                    if "Name:" in line:
                        student_name = line.replace("Name:", "").strip()
                    if "Message:" in line:
                        message_body = line.replace("Message:", "").strip()
                
                # إذا لم ينجح التقسيم، نأخذ النص كله
                if message_body == "":
                    message_body = result_text

                # البحث عن رقم ولي الأمر
                parent_phone = ""
                # هنا نبحث عن جزء من الاسم داخل الملف
                match = parents_df[parents_df['Student_Name'].str.contains(student_name, na=False)]
                
                if not match.empty:
                    parent_phone = match.iloc[0]['Parent_Phone']
                    st.success(f"تم العثور على رقم ولي أمر الطالب: {student_name}")
                    
                    # إنشاء رابط واتساب
                    encoded_message = urllib.parse.quote(message_body)
                    whatsapp_link = f"https://wa.me/{parent_phone}?text={encoded_message}"
                    
                    # زر الإرسال الكبير
                    st.markdown(f"""
                    <a href="{whatsapp_link}" target="_blank">
                        <button style="background-color:#25D366; color:white; padding:15px 32px; border:none; border-radius:4px; font-size:16px; cursor:pointer;">
                            إرسال عبر واتساب 📱
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"لم يتم العثور على رقم لهاتف الطالب ({student_name}) في الملف. تأكد من تطابق الأسماء.")
                    st.text_area("الرسالة المقترحة (يمكنك نسخها):", message_body)

            except Exception as e:
                st.error(f"حدث خطأ: {e}")
