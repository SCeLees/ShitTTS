import pyttsx3
import os
import platform
import json
import glob
import re

def clear_screen():
    """跨平台清屏"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def initialize_engine(rate=150, volume=1.0, voice_id=None):
    """初始化语音引擎，支持指定 voice_id"""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        # 如果指定了 voice_id，尝试使用
        if voice_id:
            voices = engine.getProperty('voices')
            valid_voice = None
            for voice in voices:
                if voice.id == voice_id:
                    valid_voice = voice
                    break
            if valid_voice:
                engine.setProperty('voice', voice_id)
            else:
                print(f"警告：未找到指定的语音ID '{voice_id}'，使用默认语音。")
        else:
            # 未指定 voice_id 时，优先选择中文语音
            voices = engine.getProperty('voices')
            chinese_voice = None
            for voice in voices:
                if "Chinese" in voice.name or "Chinese" in voice.id or "Mandarin" in voice.name:
                    chinese_voice = voice
                    break
            if chinese_voice:
                engine.setProperty('voice', chinese_voice.id)
            else:
                print("警告：未找到中文语音，可能使用默认语音。")
        return engine
    except Exception as e:
        print(f"初始化语音引擎失败：{e}")
        return None

def text_to_speech(text, rate, volume, voice_id=None):
    """朗读文本，支持指定 voice_id"""
    engine = initialize_engine(rate, volume, voice_id)
    if not engine:
        return
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"朗读出错：{e}")
    finally:
        try:
            engine.stop()
        except:
            pass

def list_voices():
    """列出所有可用的语音"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if not voices:
            print("未检测到任何语音。")
            return
        print("\n可用语音列表：")
        print(f"{'编号':<4} {'名称':<30} {'语言':<15} {'ID'}")
        print("=" * 80)
        for i, voice in enumerate(voices):
            lang = ', '.join(voice.languages) if voice.languages else 'Unknown'
            print(f"{i+1:<4} {voice.name[:29]:<30} {lang:<15} {voice.id}")
        print("=" * 80)
        print("使用 ':voice select <编号>' 选择语音")
    except Exception as e:
        print(f"获取语音列表失败：{e}")

def select_voice_by_index(index):
    """根据编号选择语音"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        if 1 <= index <= len(voices):
            selected = voices[index - 1]
            print(f"✅ 已选择语音：{selected.name}")
            return selected.id  # 返回 voice_id
        else:
            print(f"❌ 编号超出范围，有效范围是 1-{len(voices)}")
            return None
    except Exception as e:
        print(f"选择语音失败：{e}")
        return None

def read_text_file(file_paths):
    """读取多个 TXT 文件并按空行分块"""
    blocks = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # 以空行分隔文本块
                file_blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
                blocks.extend(file_blocks)
                print(f"已加载文件：{file_path}，包含 {len(file_blocks)} 个文本块")
        except FileNotFoundError:
            print(f"错误：文件 '{file_path}' 不存在")
        except UnicodeDecodeError:
            try:
                # 尝试其他编码
                with open(file_path, 'r', encoding='gbk') as file:
                    content = file.read()
                    file_blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
                    blocks.extend(file_blocks)
                    print(f"已加载文件：{file_path}，包含 {len(file_blocks)} 个文本块")
            except:
                print(f"读取文件 '{file_path}' 出错：编码问题")
        except Exception as e:
            print(f"读取文件 '{file_path}' 出错：{e}")
    return blocks if blocks else None

def load_config():
    """加载配置文件"""
    config_file = 'config.json'
    default_config = {'rate': 150, 'volume': 1.0, 'recent_files': [], 'voice_id': None}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 确保兼容旧配置
                config.setdefault('voice_id', None)
                return config
        except Exception as e:
            print(f"加载配置文件出错：{e}，使用默认设置")
    return default_config

def save_config(rate, volume, recent_files, voice_id=None):
    """保存配置文件"""
    config = {'rate': rate, 'volume': volume, 'recent_files': recent_files, 'voice_id': voice_id}
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存配置文件出错：{e}")

def scan_txt_files():
    """扫描当前目录下的所有txt文件（确保不重复）"""
    txt_files = []
    seen_files = set()
    patterns = ["*.txt", "*.TXT", "*.Txt", "*.tXt", "*.txT", "*.TXt", "*.TxT", "*.tXT"]
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            abs_path = os.path.abspath(file)
            if abs_path not in seen_files:
                seen_files.add(abs_path)
                txt_files.append(file)
    return sorted(txt_files)

def display_file_list(txt_files):
    """显示文件列表"""
    if not txt_files:
        print("当前目录下没有找到txt文件")
        return
    print("\n当前目录下的txt文件:")
    print("=" * 60)
    for i, file in enumerate(txt_files, 1):
        try:
            size = os.path.getsize(file)
            size_str = f"{size} bytes"
            if size > 1024:
                size_str = f"{size/1024:.1f} KB"
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f} MB"
            print(f"{i:2d}. {file.ljust(40)} ({size_str})")
        except:
            print(f"{i:2d}. {file}")
    print("=" * 60)
    print("使用 ':file <编号>' 命令选择文件")

def display_help():
    """显示帮助信息"""
    clear_screen()
    print("""
文本转语音程序 - 使用说明
================================
命令前缀: 所有命令以冒号(:)开头
- 手动输入模式：
  - 直接输入文本，按回车朗读。
- 文件读取模式：
  - 输入 ':file <路径1> <路径2> ...' 加载多个 TXT 文件
  - 输入 ':file <编号>' 选择当前目录下的txt文件
  - 输入 ':list' 显示当前目录下的txt文件列表
  - 内容以空行分块，每块文本显示后，按回车朗读
  - 命令：
    - :back：回退到上一块
    - :next：继续到下一块（或直接回车）
    - :goto <编号>：跳转到指定块
    - :manual：切换回手动输入
- 音色控制：
  - :voices：列出所有可用语音
  - :voice select <编号>：选择指定编号的语音
- 其他命令：
  - :rate <数值>：设置语速（50-300，推荐150）
  - :volume <数值>：设置音量（0.0-1.0）
  - :help：显示此帮助信息
  - :about: 查看关于本项目的信息
  - :clear：清屏
  - :quit/:exit：退出程序
================================
    """)

def display_text_block(block, index, total, blocks):
    """显示文本块内容及前后块摘要"""
    print(f"\n=== 第 {index + 1}/{total} 块文本 ===")
    print(block)
    print("=" * 40)
    if index > 0:
        prev_summary = blocks[index - 1][:50] + ("..." if len(blocks[index - 1]) > 50 else "")
        print(f"上一块摘要（{index}/{total}）：{prev_summary}")
    if index < total - 1:
        next_summary = blocks[index + 1][:50] + ("..." if len(blocks[index + 1]) > 50 else "")
        print(f"下一块摘要（{index + 2}/{total}）：{next_summary}")
    print("=" * 40)
    print("按回车朗读此块，输入 ':back'、':next'、':goto <编号>' 或 ':manual'")

def process_command(user_input, txt_files):
    """处理用户输入的命令"""
    if not user_input.startswith(':'):
        return None, user_input
    parts = user_input[1:].split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return command, args

def main():
    config = load_config()
    rate = config.get('rate', 150)
    volume = config.get('volume', 1.0)
    recent_files = config.get('recent_files', [])
    saved_voice_id = config.get('voice_id', None)  # 从配置加载 voice_id
    file_mode = False
    text_blocks = []
    current_block_index = 0
    txt_files = scan_txt_files()
    clear_screen()
    print("欢迎使用ShitTTS-CLI文本转语音程序！\n"
          "输入 ':help' 查看使用说明，':quit' 或 ':exit' 退出。\n"
          "输入 ':voices'查看可用音色\n"
          "输入 ':rate <数值>'设置语速（50-300，推荐150）\n"
          "输入 ':volume <数值>'设置音量（0.0-1.0）\n")
    if recent_files:
        print(f"最近打开的文件：{', '.join(recent_files[-3:])}")

    while True:
        try:
            if file_mode and text_blocks:
                if current_block_index < len(text_blocks):
                    display_text_block(text_blocks[current_block_index], current_block_index, len(text_blocks), text_blocks)
                else:
                    print(f"已到达最后一块文本（共 {len(text_blocks)} 块）")
                    file_mode = False
                    text_blocks = []
                    current_block_index = 0
                    print("已切换回手动输入模式")
                    continue

            user_input = input("> ").strip()
            command, args = process_command(user_input, txt_files)

            if command in ['quit', 'exit', '退出']:
                save_config(rate, volume, recent_files, voice_id=saved_voice_id)
                print("程序已退出")
                break

            if command == 'help':
                display_help()
                continue

            if command == 'clear':
                clear_screen()
                continue

            if command == 'rate':
                try:
                    new_rate = int(args)
                    if 50 <= new_rate <= 300:
                        rate = new_rate
                        print(f"语速已设置为：{rate}")
                        save_config(rate, volume, recent_files, voice_id=saved_voice_id)
                    else:
                        print("语速范围应为 50-300")
                except (IndexError, ValueError):
                    print("请输入有效语速值，例如：:rate 150")
                continue

            if command == 'volume':
                try:
                    new_volume = float(args)
                    if 0.0 <= new_volume <= 1.0:
                        volume = new_volume
                        print(f"音量已设置为：{volume}")
                        save_config(rate, volume, recent_files, voice_id=saved_voice_id)
                    else:
                        print("音量范围应为 0.0-1.0")
                except (IndexError, ValueError):
                    print("请输入有效音量值，例如：:volume 1.0")
                continue

            if command == 'file':
                if not args:
                    print("请输入文件路径或编号，例如：:file example.txt 或 :file 1")
                    continue
                if args.isdigit():
                    file_index = int(args) - 1
                    if 0 <= file_index < len(txt_files):
                        file_paths = [txt_files[file_index]]
                    else:
                        print(f"无效的文件编号，请输入 1-{len(txt_files)} 之间的数字")
                        continue
                else:
                    file_paths = args.split()
                if file_paths:
                    text_blocks = read_text_file(file_paths)
                    if text_blocks:
                        file_mode = True
                        current_block_index = 0
                        for file_path in file_paths:
                            if file_path in recent_files:
                                recent_files.remove(file_path)
                            recent_files.append(file_path)
                        recent_files = recent_files[-5:]
                        save_config(rate, volume, recent_files, voice_id=saved_voice_id)
                        print(f"已加载 {len(file_paths)} 个文件，共有 {len(text_blocks)} 块文本")
                    else:
                        file_mode = False
                continue

            if command == 'list':
                txt_files = scan_txt_files()
                display_file_list(txt_files)
                continue

            if command == 'about':
                clear_screen()
                print("""
                ShitTTS-CLI

                版本：v1.14.51.4-cli
                作者：GTSense/DeepSeek
                我的个人主页：https://gts.us.kg
                GitHub：https://github.com/SCeLees/ShitTTS

                这是一个基于Pyttsx3的语音合成器应用程序。

                为什么要开发这个程序？
                为了免去完成E听说模拟考试作业的麻烦，我找到了一款可以自动获取答案的工具，
                如果能将答案文本转换为语音，又能够自动朗读答案，也无需自己开口那就好了。
                但是那些TTS软件用起来也太麻烦了，直接调用系统的TTS也很麻烦！
                所以我使用AI工具开发了这个项目，基于Pyttsx3实现TTS语音合成，
                再借助Voicemeeter将音频输出到虚拟麦克风中，从而模拟人声完成作业。

                使用说明：
                1. 在"合成"页面输入或导入文本
                2. 选择喜欢的音色、语速和音量
                3. 点击"朗读全文"或"分块朗读"开始语音合成
                4. 使用空行来分块

                本项目仅供参考，请使用更强大的TTS软件。

                Copyright © 2025 GTSense. Licensed under MIT
                """)
                continue

            # === 音色选择命令 ===
            if command == 'voices':
                list_voices()
                continue

            if command == 'voice' and args.startswith('select'):
                try:
                    idx = int(args.split()[-1])
                    selected_id = select_voice_by_index(idx)
                    if selected_id is not None:
                        saved_voice_id = selected_id  # 更新全局保存的 voice_id
                        save_config(rate, volume, recent_files, voice_id=saved_voice_id)
                except (ValueError, IndexError):
                    print("请指定有效的语音编号，例如：:voice select 1")
                continue
            # ============================

            if file_mode:
                if command == 'back':
                    if current_block_index > 0:
                        current_block_index -= 1
                    else:
                        print("已经是第一块文本")
                    continue
                elif command == 'next' or user_input == '':
                    if current_block_index < len(text_blocks):
                        text_to_speech(text_blocks[current_block_index], rate, volume, voice_id=saved_voice_id)
                        current_block_index += 1
                    continue
                elif command == 'goto':
                    try:
                        block_num = int(args)
                        if 1 <= block_num <= len(text_blocks):
                            current_block_index = block_num - 1
                        else:
                            print(f"请输入有效块编号（1-{len(text_blocks)}）")
                    except (IndexError, ValueError):
                        print("请输入有效块编号，例如：:goto 3")
                    continue
                elif command == 'manual':
                    file_mode = False
                    text_blocks = []
                    current_block_index = 0
                    print("已切换回手动输入模式")
                    continue
                elif command is not None:
                    print(f"未知命令: :{command}")
                    continue

            if user_input and command is None:
                text_to_speech(user_input, rate, volume, voice_id=saved_voice_id)
            elif not user_input:
                print("请输入有效文本或命令！")

        except KeyboardInterrupt:
            save_config(rate, volume, recent_files, voice_id=saved_voice_id)
            print("\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误：{e}")

if __name__ == "__main__":
    main()
