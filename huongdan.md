# Hướng dẫn chi tiết hoàn thành Lab 20: Multi-Agent Research System

Tài liệu này cung cấp các hướng dẫn từng bước (step-by-step) để bạn có thể hoàn thiện các phần `TODO(student)` trong repo này một cách tốt nhất. 

> **Lưu ý quan trọng**: Đừng quên tạo môi trường ảo, cài đặt requirements (`pip install -e "[dev]"`) và copy file `.env.example` sang `.env` điền các API KEY cần thiết trước khi code.

---

## Bước 1: Khởi tạo LLM Client (Baseline)

📍 **File cần sửa:** `src/multi_agent_research_lab/services/llm_client.py`

Đây là trái tim của hệ thống, nơi giao tiếp với các mô hình ngôn ngữ (OpenAI, Gemini,...).

**Cách làm:**
1. Thư viện gợi ý: Sử dụng `openai` SDK (nếu dùng OpenAI) hoặc có thể dùng `langchain_openai`. 
2. Trong hàm `complete(self, system_prompt: str, user_prompt: str) -> LLMResponse`:
   - Tạo messages object gồm vai trò `system` và `user`.
   - Gọi API chat completion (ví dụ: `client.chat.completions.create(...)`).
   - Lấy `content` từ response.
   - Trích xuất token usage (nếu provider có hỗ trợ) để lưu vào `input_tokens` và `output_tokens`.
   - Tính toán `cost_usd` dựa trên số lượng token và giá của model bạn đang dùng.
   - Return object `LLMResponse`.
3. Nhớ implement thêm Try/Catch để handle lỗi API (Timeout, Rate limit) và Retry logic nếu cần.

---

## Bước 2: Thiết kế Supervisor (Điều phối viên)

📍 **File cần sửa:** `src/multi_agent_research_lab/agents/supervisor.py`

Supervisor không tự sinh ra câu trả lời, mà đóng vai trò như một **Router**, xem xét `ResearchState` hiện tại và quyết định gọi ai tiếp theo.

**Cách làm:**
1. Trong hàm `run(self, state: ResearchState)`:
   - Kiểm tra **Guardrails**: Nếu `state.iteration` đã vượt quá số lượt tối đa -> trả về kết quả hoặc ép chuyển sang `writer`.
   - **Định tuyến (Routing)**:
     - Nếu `state.research_notes` rỗng -> trả về lệnh chuyển tiếp sang `researcher`.
     - Nếu đã có thông tin nghiên cứu nhưng `state.analysis_notes` rỗng -> chuyển sang `analyst`.
     - Nếu đã phân tích xong nhưng chưa có câu trả lời -> chuyển sang `writer`.
     - Nếu đã có `final_answer` -> báo hoàn thành (`done` hoặc `END`).
2. Có thể hard-code rule-based bằng if/else (đơn giản) hoặc dùng LLM để LLM tự suy luận xem nên gọi ai tiếp (nâng cao).

---

## Bước 3: Hoàn thiện LangGraph Workflow

📍 **File cần sửa:** `src/multi_agent_research_lab/graph/workflow.py`

Đây là nơi bạn "nối" các Agent rời rạc lại với nhau thành một đồ thị vòng lặp.

**Cách làm:**
1. Trong hàm `build()`:
   - Dùng `from langgraph.graph import StateGraph, END`.
   - Tạo graph: `workflow = StateGraph(ResearchState)`.
   - Thêm các Nodes: `workflow.add_node("supervisor", supervisor_node)`, tương tự cho `researcher`, `analyst`, `writer`.
   - Cài đặt Start Node: `workflow.set_entry_point("supervisor")`.
   - Thêm các Conditional Edges: Từ `supervisor`, nếu quyết định là 'researcher' thì trỏ đến node `researcher`, tương tự cho các node khác và hướng dẫn trở về lại `supervisor` sau khi worker hoàn thành.
   - Biên dịch graph: `app = workflow.compile()`.
2. Trong hàm `run()`:
   - Gọi `app.invoke(state.model_dump())` hoặc pass thẳng `state` tuỳ theo việc implement state graph.
   - Parse kết quả trả về lại object `ResearchState`.

---

## Bước 4: Viết các Worker Agents

📍 **File cần sửa:** `src/multi_agent_research_lab/agents/researcher.py`, `analyst.py`, `writer.py`

Mỗi agent cần một `system_prompt` thật sắc bén để làm đúng nhiệm vụ.

**Cách làm:**
1. Khởi tạo `LLMClient` bên trong agent (hoặc truyền qua constructor).
2. Viết `system_prompt` riêng biệt cho từng người:
   - **Researcher**: "Bạn là chuyên gia thu thập dữ liệu. Hãy tạo ra các query tìm kiếm hoặc tổng hợp thông tin về chủ đề được yêu cầu." (Có thể gọi thêm web search).
   - **Analyst**: "Bạn là nhà phân tích. Đọc các research notes sau và rút ra insight quan trọng nhất, tìm ra các điểm mâu thuẫn."
   - **Writer**: "Bạn là tác giả. Đọc analysis notes và yêu cầu ban đầu để viết một báo cáo hoàn chỉnh dài 500 từ."
3. Lấy dữ liệu từ `state`, gọi `llm_client.complete()`.
4. Cập nhật kết quả vào đúng field tương ứng trong `state` (ví dụ `state.research_notes = response.content`).
5. Cập nhật `state.agent_results` và gọi `state.add_trace_event(...)` để log lại quá trình.

---

## Bước 5: Tracing và Benchmark (Quan trọng nhất)

📍 **File cần sửa:** `src/multi_agent_research_lab/evaluation/benchmark.py` & `reports/benchmark_report.md`

Hệ thống multi-agent thường chậm hơn và tốn tiền hơn, nên bạn phải chứng minh nó mang lại Quality tốt hơn baseline.

**Cách làm:**
1. Chạy CLI ở mode `baseline`: 
   `python -m multi_agent_research_lab.cli baseline --query "..."`
2. Chạy CLI ở mode `multi-agent`:
   `python -m multi_agent_research_lab.cli multi-agent --query "..."`
3. Ghi nhận các số liệu:
   - **Thời gian (Latency):** Mất bao nhiêu giây?
   - **Chi phí (Cost/Tokens):** Tiêu thụ bao nhiêu token?
   - **Chất lượng:** Độ sâu của thông tin, số lượng nguồn được trích dẫn.
4. Tổng hợp và điền vào bảng so sánh trong file `reports/benchmark_report.md`. Nêu rõ failure modes và lý do so sánh.

---

## 💡 Các lỗi (Failure modes) thường gặp và cách Fix
- **Lỗi vòng lặp vô hạn (Infinite Loop):** Supervisor liên tục gọi lại Researcher mà không bao giờ qua Writer. -> *Cách fix:* Dùng `state.iteration` để đếm, nếu quá 3-5 lần thì ép Supervisor trỏ thẳng đến Writer.
- **Agent quên mất Context ban đầu:** Writer chỉ đọc Analysis mà quên mất câu hỏi của user. -> *Cách fix:* Luôn inject `state.request` vào trong prompt của mọi agents.
- **Quá rập khuôn (Format lộn xộn):** Các LLM trả về format không mong muốn. -> *Cách fix:* Yêu cầu rõ trong `system_prompt` (vd: "Luôn trả về định dạng JSON") hoặc sử dụng Structured Outputs.
