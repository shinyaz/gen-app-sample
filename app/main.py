import boto3
import streamlit as st
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import BedrockChat
from PyPDF2 import PdfReader

session = boto3.Session(region_name='ap-northeast-1')
bedrock_runtime = session.client(service_name="bedrock-runtime")

st.title("💬 業務報告に対する質問生成 🤔")

with st.sidebar:
    st.title("基本設定項目")
    qnum = st.number_input("生成する質問数", min_value=1, max_value=10, value=5)
    temperature = st.sidebar.slider(
        "ランダム性", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
    doc_type = st.sidebar.radio("質問生成のための情報入力タイプ", ("PDF","直接入力"))


def generate_document(form, doc_type):
    document = ""
    if doc_type == "PDF":
        default_page = 5
        uploaded_file = form.file_uploader(
            label="質問生成の元となる PDF アップロード",
            type="pdf"
        )
        form.warning(
            f"デフォルトでは最初の {default_page} ページが使われます。これは詳細設定で変更できます。ただし、文字数が非常に多い場合にはエラーとなりますのでご注意ください。", icon="⚠️")
        with form.expander("詳細設定"):
            first_page = st.number_input("最初のページ", value=1, min_value=1)
            last_page = st.number_input(
                "最後のページ", value=default_page, min_value=1)

        if uploaded_file:
            pdf_reader = PdfReader(uploaded_file)
            document = '\n\n'.join([page.extract_text()
                                    for page in pdf_reader.pages[first_page-1:last_page]])
    elif doc_type == "直接入力":
        document = form.text_area(label="回答の元となる情報を入力")
    return document


def generate_response(document):
    chat = BedrockChat(
        client=bedrock_runtime,
        model_id="anthropic.claude-v2:1",
        model_kwargs={
            "temperature": temperature,
            "max_tokens_to_sample": 2048
        }
    )
    with st.spinner("質問を生成しています..."):
        result = chat.invoke(
            [
                SystemMessage(content="""
                あなたは、ある会社の非常に賢く優秀なマネージャーです。
                あなたの部下の業務内容やその活動に関する情報を提供が提供されるので、その情報から部下の活動や業績に注意深く読み取った上で回答してください。
                """),
                HumanMessage(content=f"""`
                <文章>を元に<手順>に従って業務報告の場における質問を考えなさい。

                <文章>
                {document}
                </文章>

                <手順>
                * 必ず<文章>に関連していて具体的である必要があります。<文章>から読み取れないことは絶対に作成しないでください。
                * 質問の数は{qnum}個で箇条書きにしてください。
                * 作成した質問以外の文字列は一切出力しないでください。例外はありません。
                </手順>
                """)
            ]
        )
    st.chat_message("assistant").write(result.content)


st.chat_message("assistant").write("教えてくれた情報をもとに業務報告の場で聞かれそうな質問を作成してみるね！")

genq_form = st.form("genq_form")
document = generate_document(genq_form, doc_type)
submitted = genq_form.form_submit_button("質問生成！")
if submitted:
    generate_response(document)
