import pyttsx3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time
import webbrowser

class VoiceSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("ShitTTS-GUI文本转语音程序")
        self.root.geometry("600x700")  # 增加窗口高度以适应新功能
        self.root.resizable(True, True)

        # 语音队列和线程控制
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.stop_requested = False
        
        # 分块朗读相关变量
        self.text_blocks = []
        self.current_block_index = 0
        self.is_chunk_mode = False
        
        # 初始化语音引擎
        self.engine = None
        self.init_engine()
        
        # 获取可用声音
        self.voices = self.engine.getProperty('voices') if self.engine else []
        if not self.voices:
            messagebox.showwarning("警告", "未找到可用的语音")
        
        # 创建选项卡界面
        self.create_notebook()
        
        # 设置默认值
        if self.voices:
            self.update_voice_details(0)
        
        # 启动语音处理线程
        self.start_speech_thread()
    
    def create_notebook(self):
        """创建选项卡界面"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建合成选项卡
        self.synth_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.synth_frame, text="合成")
        
        # 创建关于选项卡
        self.about_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.about_frame, text="关于")
        
        # 创建合成页面内容
        self.create_synth_widgets()
        
        # 创建关于页面内容
        self.create_about_widgets()
    
    def create_synth_widgets(self):
        """创建合成页面内容"""
        # 主框架
        main_frame = ttk.Frame(self.synth_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 导入文件按钮
        ttk.Button(main_frame, text="导入txt文件", command=self.import_txt_file).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        # 声音选择
        ttk.Label(main_frame, text="选择音色:").grid(row=0, column=1, sticky=tk.W, pady=5, padx=(20, 0))
        self.voice_var = tk.StringVar()
        self.voice_cb = ttk.Combobox(main_frame, textvariable=self.voice_var, state="readonly", width=25)
        self.voice_cb.grid(row=0, column=2, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        if self.voices:
            self.voice_cb['values'] = [f"{voice.name} ({voice.id})" for voice in self.voices]
            self.voice_cb.current(0)
        self.voice_cb.bind('<<ComboboxSelected>>', self.on_voice_select)
        
        # 语音详情
        details_frame = ttk.LabelFrame(main_frame, text="语音详情", padding="5")
        details_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.details_text = tk.Text(details_frame, height=6, width=50)
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 语速控制
        ttk.Label(main_frame, text="语速:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.rate_var = tk.IntVar(value=150)
        self.rate_scale = ttk.Scale(main_frame, from_=50, to=300, variable=self.rate_var, 
                                   orient=tk.HORIZONTAL)
        self.rate_scale.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        self.rate_value_label = ttk.Label(main_frame, text="150")
        self.rate_value_label.grid(row=2, column=3, padx=(5, 0))
        self.rate_scale.bind("<Motion>", self.update_rate_label)
        
        # 音量控制
        ttk.Label(main_frame, text="音量:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.volume_scale = ttk.Scale(main_frame, from_=0.0, to=1.0, variable=self.volume_var, 
                                     orient=tk.HORIZONTAL)
        self.volume_scale.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        self.volume_value_label = ttk.Label(main_frame, text="1.0")
        self.volume_value_label.grid(row=3, column=3, padx=(5, 0))
        self.volume_scale.bind("<Motion>", self.update_volume_label)
        
        # 文本输入
        ttk.Label(main_frame, text="输入要朗读的文本:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 增加文本框高度，添加滚动条
        self.text_entry = tk.Text(text_frame, height=15, width=50, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_entry.yview)
        self.text_entry.configure(yscrollcommand=scrollbar.set)
        
        self.text_entry.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 添加鼠标滚轮支持
        self.text_entry.bind("<MouseWheel>", self.on_mousewheel)
        
        self.text_entry.insert("1.0", "欢迎使用ShitTTS-GUI文本转语音程序"
                                "\n\n"
                               "使用空行进行分块")
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="朗读全文", command=self.speak_full).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="分块朗读", command=self.speak_chunks).pack(side=tk.LEFT, padx=5)
        
        # 分块控制框架
        chunk_control_frame = ttk.Frame(main_frame)
        chunk_control_frame.grid(row=7, column=0, columnspan=4, pady=5)
        
        self.prev_chunk_button = ttk.Button(chunk_control_frame, text="上一块", command=self.speak_prev_chunk, state=tk.DISABLED)
        self.prev_chunk_button.pack(side=tk.LEFT, padx=5)
        
        self.next_chunk_button = ttk.Button(chunk_control_frame, text="下一块", command=self.speak_next_chunk, state=tk.DISABLED)
        self.next_chunk_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(chunk_control_frame, text="跳转到第").pack(side=tk.LEFT, padx=(10, 5))
        self.chunk_number_var = tk.StringVar()
        self.chunk_number_entry = ttk.Entry(chunk_control_frame, textvariable=self.chunk_number_var, width=5)
        self.chunk_number_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(chunk_control_frame, text="块").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chunk_control_frame, text="跳转", command=self.speak_specific_chunk).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="停止", command=self.stop).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="就绪")
        self.status_label.grid(row=8, column=0, columnspan=4, pady=5)
        
        # 配置网格权重
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(5, weight=1)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
    
    def create_about_widgets(self):
        """创建关于页面内容"""
        # 主框架
        main_frame = ttk.Frame(self.about_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="ShitTTS-GUI", font=("Arial", 16, "bold"))
        title_label.pack(pady=(20, 10))
        
        # 版本信息
        version_label = ttk.Label(main_frame, text="版本: v1.14.51.4-gui", font=("Arial", 10))
        version_label.pack(pady=5)
        
        # 作者信息
        author_label = ttk.Label(main_frame, text="作者: GTSense/DeepSeek", font=("Arial", 10))
        author_label.pack(pady=5)
        
        # 博客链接
        blog_frame = ttk.Frame(main_frame)
        blog_frame.pack(pady=5)
        
        ttk.Label(blog_frame, text="我的个人主页:").pack(side=tk.LEFT)
        blog_link = ttk.Label(blog_frame, text="https://gts.us.kg  ", foreground="blue", cursor="hand2")
        blog_link.pack(side=tk.LEFT, padx=(5, 0))
        blog_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://gts.us.kg  "))
        
        # GitHub链接
        github_frame = ttk.Frame(main_frame)
        github_frame.pack(pady=5)
        
        ttk.Label(github_frame, text="GitHub:").pack(side=tk.LEFT)
        github_link = ttk.Label(github_frame, text="https://github.com/SCeLees  ", foreground="blue", cursor="hand2")
        github_link.pack(side=tk.LEFT, padx=(5, 0))
        github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/yourusername  "))

        # 说明文本
        description = """
这是一个基于Pyttsx3的语音合成器应用程序。

为什么要开发这个程序？
    为了免去完成E听说模拟考试作业的麻烦，我找到了一款可以自动获取答案的工具，
    如果既能将答案文本转换为语音，又能够自动朗读答案，也无需自己开口那就好了。
    但是那些TTS软件用起来也太麻烦了，直接调用系统的TTS也很麻烦！
    所以我使用AI工具开发了这个项目，基于Pyttsx3实现TTS语音合成，
    再借助Voicemeeter将音频输出到虚拟麦克风中，从而模拟人声完成作业。
 
使用说明:
1. 在"合成"页面输入或导入文本
2. 选择喜欢的音色、语速和音量
3. 点击"朗读全文"或"分块朗读"开始语音合成
4. 使用空行来分块

本项目仅供参考，请使用更强大的TTS软件。
        """
        
        desc_label = ttk.Label(main_frame, text=description, justify=tk.LEFT)
        desc_label.pack(pady=20, padx=20)
        
        # 版权信息
        copyright_label = ttk.Label(main_frame, text="Copyright © 2025 GTSense. Licensed under MIT.", font=("Arial", 8))
        copyright_label.pack(side=tk.BOTTOM, pady=10)
    
    def on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.text_entry.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def init_engine(self):
        """初始化语音引擎"""
        try:
            self.engine = pyttsx3.init()
            # 设置默认属性
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"初始化语音引擎失败: {str(e)}")
            self.engine = None
            return False
    
    def start_speech_thread(self):
        """启动语音处理线程"""
        self.speech_thread = threading.Thread(target=self.speech_worker, daemon=True)
        self.speech_thread.start()
    
    def speech_worker(self):
        """语音处理工作线程"""
        while True:
            try:
                if not self.speech_queue.empty():
                    text, rate, volume, voice_id = self.speech_queue.get()
                    
                    # 每次都需要重新初始化引擎
                    if not self.init_engine():
                        continue
                    
                    # 设置属性
                    self.engine.setProperty('rate', rate)
                    self.engine.setProperty('volume', volume)
                    if voice_id:
                        self.engine.setProperty('voice', voice_id)
                    
                    # 更新界面状态
                    self.root.after(0, lambda: self.status_label.config(text="朗读中..."))
                    
                    # 执行朗读
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                    
                    # 完成后的处理
                    self.is_speaking = False
                    if not self.stop_requested:
                        self.root.after(0, lambda: self.status_label.config(text="朗读完成"))
                        # 如果是分块模式，朗读完成后启用按钮
                        if self.is_chunk_mode:
                            self.root.after(0, self.enable_chunk_buttons)
                    else:
                        self.root.after(0, lambda: self.status_label.config(text="已停止"))
                        self.stop_requested = False
                    
                    # 清理引擎
                    self.engine = None
                
                time.sleep(0.1)  # 避免CPU占用过高
                
            except Exception as e:
                print(f"语音线程错误: {e}")
                self.is_speaking = False
                self.engine = None
                time.sleep(0.1)
    
    def import_txt_file(self):
        """导入txt文件"""
        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_entry.delete("1.0", tk.END)
                    self.text_entry.insert("1.0", content)
                self.status_label.config(text=f"已导入文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件时出错: {str(e)}")
    
    def on_voice_select(self, event):
        index = self.voice_cb.current()
        self.update_voice_details(index)
    
    def update_voice_details(self, index):
        if index < 0 or index >= len(self.voices):
            return
            
        voice = self.voices[index]
        details = f"ID: {voice.id}\n"
        details += f"名称: {voice.name}\n"
        details += f"语言: {voice.languages[0] if voice.languages else '未知'}\n"
        details += f"性别: {voice.gender}\n"
        details += f"年龄: {voice.age}"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
    
    def update_rate_label(self, event):
        self.rate_value_label.config(text=str(self.rate_var.get()))
    
    def update_volume_label(self, event):
        value = self.volume_var.get()
        self.volume_value_label.config(text=f"{value:.1f}")
    
    def split_text_into_blocks(self, text):
        """将文本按空行分割成块"""
        blocks = []
        current_block = []
        
        for line in text.split('\n'):
            if line.strip() == '':
                if current_block:  # 如果当前块不为空
                    blocks.append('\n'.join(current_block))
                    current_block = []
            else:
                current_block.append(line)
        
        # 添加最后一个块（如果有）
        if current_block:
            blocks.append('\n'.join(current_block))
            
        return blocks
    
    def speak_full(self):
        """朗读全文"""
        if self.is_speaking:
            messagebox.showinfo("提示", "正在朗读中，请等待完成或点击停止")
            return
        
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入要朗读的文本")
            return
        
        # 获取当前选择的语音
        voice_id = None
        if self.voices and self.voice_cb.current() >= 0:
            voice_id = self.voices[self.voice_cb.current()].id
        
        # 将朗读任务加入队列
        self.is_chunk_mode = False
        self.speech_queue.put((text, self.rate_var.get(), self.volume_var.get(), voice_id))
        self.status_label.config(text="已加入队列")
    
    def speak_chunks(self):
        """分块朗读"""
        if self.is_speaking:
            messagebox.showinfo("提示", "正在朗读中，请等待完成或点击停止")
            return
        
        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入要朗读的文本")
            return
        
        # 分割文本为块
        self.text_blocks = self.split_text_into_blocks(text)
        if not self.text_blocks:
            messagebox.showwarning("警告", "没有找到有效的文本块")
            return
        
        self.current_block_index = 0
        self.is_chunk_mode = True
        
        # 启用分块控制按钮
        self.prev_chunk_button.config(state=tk.DISABLED)
        self.next_chunk_button.config(state=tk.NORMAL)
        
        # 开始朗读第一块
        self.speak_current_chunk()
    
    def speak_current_chunk(self):
        """朗读当前块文本"""
        if self.current_block_index >= len(self.text_blocks) or self.current_block_index < 0:
            messagebox.showinfo("提示", "没有可朗读的文本块")
            return
        
        # 获取当前块文本
        text_block = self.text_blocks[self.current_block_index]
        
        # 获取当前选择的语音
        voice_id = None
        if self.voices and self.voice_cb.current() >= 0:
            voice_id = self.voices[self.voice_cb.current()].id
        
        # 将朗读任务加入队列
        self.speech_queue.put((text_block, self.rate_var.get(), self.volume_var.get(), voice_id))
        self.status_label.config(text=f"朗读第 {self.current_block_index + 1}/{len(self.text_blocks)} 块")
        
        # 禁用按钮，直到当前块朗读完成
        self.prev_chunk_button.config(state=tk.DISABLED)
        self.next_chunk_button.config(state=tk.DISABLED)
    
    def speak_prev_chunk(self):
        """朗读上一块文本"""
        if not self.is_chunk_mode or not self.text_blocks:
            return
            
        if self.current_block_index > 0:
            self.current_block_index -= 1
            self.speak_current_chunk()
        else:
            messagebox.showinfo("提示", "已经是第一块了")
    
    def speak_next_chunk(self):
        """朗读下一块文本"""
        if not self.is_chunk_mode or not self.text_blocks:
            return
            
        if self.current_block_index < len(self.text_blocks) - 1:
            self.current_block_index += 1
            self.speak_current_chunk()
        else:
            messagebox.showinfo("提示", "已经是最后一块了")
    
    def speak_specific_chunk(self):
        """跳转到指定块并朗读"""
        if not self.is_chunk_mode or not self.text_blocks:
            return
            
        try:
            chunk_number = int(self.chunk_number_var.get())
            if 1 <= chunk_number <= len(self.text_blocks):
                self.current_block_index = chunk_number - 1
                self.speak_current_chunk()
            else:
                messagebox.showwarning("警告", f"请输入1到{len(self.text_blocks)}之间的数字")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字")
    
    def enable_chunk_buttons(self):
        """启用分块控制按钮"""
        if self.is_chunk_mode and self.text_blocks:
            # 根据当前块索引启用/禁用上一块和下一块按钮
            if self.current_block_index > 0:
                self.prev_chunk_button.config(state=tk.NORMAL)
            else:
                self.prev_chunk_button.config(state=tk.DISABLED)
                
            if self.current_block_index < len(self.text_blocks) - 1:
                self.next_chunk_button.config(state=tk.NORMAL)
            else:
                self.next_chunk_button.config(state=tk.DISABLED)
                
            self.status_label.config(text=f"第 {self.current_block_index + 1}/{len(self.text_blocks)} 块完成")

    def stop(self):
        self.stop_requested = True
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        self.status_label.config(text="停止请求已发送")
        # 停止后也禁用分块按钮
        self.prev_chunk_button.config(state=tk.DISABLED)
        self.next_chunk_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceSelector(root)
    root.mainloop()
