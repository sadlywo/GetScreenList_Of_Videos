import cv2
import os
import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def get_video_files(folder_path):
    """获取文件夹中所有视频文件"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.webm']
    video_files = []
    
    for file in os.listdir(folder_path):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(os.path.join(folder_path, file))
    
    return video_files

def format_time(seconds):
    """将秒数转换为时:分:秒格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def extract_frames(video_path, num_frames=20):
    """从视频中提取指定数量的帧"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return None, 0
    
    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    frames = []
    timestamps = []
    
    # 计算帧间隔
    frame_interval = total_frames // num_frames if total_frames > num_frames else 1
    
    for i in range(0, total_frames, frame_interval):
        if len(frames) >= num_frames:
            break
            
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        
        if ret:
            # 转换BGR到RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
            
            # 计算时间戳
            timestamp = i / fps if fps > 0 else 0
            timestamps.append(timestamp)
    
    cap.release()
    return frames, timestamps, duration

def create_thumbnail_grid(frames, timestamps, duration, video_name, grid_cols=5):
    """创建缩略图网格"""
    if not frames:
        return None
    
    # 设置缩略图尺寸
    thumb_width = 240
    thumb_height = 135
    
    # 计算网格尺寸
    grid_rows = math.ceil(len(frames) / grid_cols)
    
    # 创建画布
    canvas_width = grid_cols * thumb_width
    canvas_height = grid_rows * thumb_height + 60  # 额外空间用于标题
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), (30, 30, 30))
    draw = ImageDraw.Draw(canvas)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        title_font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # 添加标题
    title_text = f"{video_name} - 时长: {format_time(duration)}"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (canvas_width - title_width) // 2
    draw.text((title_x, 10), title_text, fill=(255, 255, 255), font=title_font)
    
    # 添加帧到网格
    for i, (frame, timestamp) in enumerate(zip(frames, timestamps)):
        row = i // grid_cols
        col = i % grid_cols
        
        # 调整帧大小
        frame_img = Image.fromarray(frame)
        frame_img = frame_img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        
        # 计算位置
        x = col * thumb_width
        y = row * thumb_height + 50  # 留出标题空间
        
        # 粘贴帧
        canvas.paste(frame_img, (x, y))
        
        # 添加时间戳
        time_text = format_time(timestamp)
        text_bbox = draw.textbbox((0, 0), time_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # 时间戳背景
        text_x = x + thumb_width - text_width - 5
        text_y = y + thumb_height - text_height - 5
        draw.rectangle([text_x - 2, text_y - 2, text_x + text_width + 2, text_y + text_height + 2], 
                      fill=(0, 0, 0, 180))
        draw.text((text_x, text_y), time_text, fill=(255, 255, 255), font=font)
    
    return canvas

def generate_video_thumbnails(folder_path, output_folder=None):
    """为文件夹中所有视频生成缩略图"""
    if output_folder is None:
        output_folder = folder_path
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    video_files = get_video_files(folder_path)
    
    if not video_files:
        print("在指定文件夹中未找到视频文件")
        return
    
    print(f"找到 {len(video_files)} 个视频文件")
    
    for video_path in video_files:
        print(f"正在处理: {os.path.basename(video_path)}")
        
        # 提取帧
        frames, timestamps, duration = extract_frames(video_path, num_frames=20)
        
        if frames:
            # 获取视频文件名（不含扩展名）
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            # 创建缩略图
            thumbnail = create_thumbnail_grid(frames, timestamps, duration, video_name)
            
            if thumbnail:
                # 保存缩略图
                output_path = os.path.join(output_folder, f"{video_name}.png")
                thumbnail.save(output_path, "PNG")
                print(f"缩略图已保存: {output_path}")
            else:
                print(f"无法创建缩略图: {video_path}")
        else:
            print(f"无法提取帧: {video_path}")

def main():
    """主函数"""
    # 设置视频文件夹路径
    video_folder = input("请输入视频文件夹路径 (直接回车使用当前目录): ").strip()
    if not video_folder:
        video_folder = os.getcwd()
    
    if not os.path.exists(video_folder):
        print("指定的文件夹不存在!")
        return
    
    # 设置输出文件夹路径（可选）
    output_folder = input("请输入输出文件夹路径 (直接回车使用视频所在目录): ").strip()
    if not output_folder:
        output_folder = video_folder
    
    print(f"视频文件夹: {video_folder}")
    print(f"输出文件夹: {output_folder}")
    print("开始生成缩略图...")
    
    generate_video_thumbnails(video_folder, output_folder)
    print("完成!")

if __name__ == "__main__":
    main()