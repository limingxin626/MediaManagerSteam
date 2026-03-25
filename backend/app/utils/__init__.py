import os
import datetime
import hashlib
import logging
import subprocess
import sys
from typing import List

logger = logging.getLogger(__name__)

# 媒体文件上传目录
MEDIA_UPLOAD_DIR = "./uploads"
os.makedirs(MEDIA_UPLOAD_DIR, exist_ok=True)

# 全局变量，用于存储当前的媒体ID列表
# 永远只维持最新的列表
current_media_list: List[int] = []

# 全局变量，用于存储当前的分组ID列表
# 永远只维持最新的列表
current_group_list: List[int] = []


# 文件处理工具类
class FileUtils:
    @staticmethod
    def save_upload_file(file, upload_dir: str = MEDIA_UPLOAD_DIR) -> str:
        """保存上传的文件并返回文件路径"""
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(upload_dir, f"{datetime.datetime.now().timestamp()}{file_extension}")
        
        with open(file_path, "wb") as f:
            f.write(file.read())
        
        return file_path
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件"""
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


def calculate_file_hash(file_path: str, size_threshold: int = 100 * 1024 * 1024) -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        size_threshold: 文件大小阈值（字节），小于此值的文件计算blake2b，大于等于此值的文件使用文件大小作为hash
    
    Returns:
        文件哈希值字符串
    """
    try:
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 当文件小于阈值的时候计算hash，否则hash就等于文件大小
        if file_size < size_threshold:
            # 小于阈值的文件直接读取到内存计算blake2b hash
            logger.info(f"Calculating blake2b hash for {file_path} (size: {file_size} bytes)")
            with open(file_path, 'rb') as f:
                return hashlib.blake2b(f.read()).hexdigest()
        else:
            # 大于等于阈值的文件使用文件大小作为hash
            return str(file_size)
    except Exception as e:
        logger.error(f"Failed to calculate file hash for {file_path}: {str(e)}")
        return ""


class ThumbnailUtils:
    """缩略图生成工具类"""
    
    @staticmethod
    def generate_image_thumbnail(source_path: str, thumb_path: str, max_size: int = 0) -> bool:
        """使用 PIL 为静态图片生成缩略图"""
        try:
            from PIL import Image
            
            with Image.open(source_path) as img:
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 缩放并保存为 WEBP 格式
                if max_size > 0:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                img.save(thumb_path, 'WEBP', quality=90)
            
            logger.info(f"Generated image thumbnail: {thumb_path}")
            return True
            
        except ImportError:
            logger.warning("PIL not installed, skipping thumbnail generation")
            return False
        except Exception as e:
            logger.error(f"Failed to generate image thumbnail: {str(e)}")
            return False
    
    @staticmethod
    def generate_video_thumbnail(source_path: str, thumb_path: str, ffmpeg_path: str, max_size: int = 300) -> bool:
        """使用 ffmpeg 为视频生成缩略图
        
        Args:
            source_path: 源视频文件路径
            thumb_path: 缩略图输出路径
            ffmpeg_path: ffmpeg 可执行文件路径
            max_size: 缩略图最大尺寸
        """
        try:
            # 在Windows上处理编码问题
            encoding = 'utf-8' if sys.platform != 'win32' else 'utf-8'
            errors = 'ignore' if sys.platform == 'win32' else 'strict'
            
            # 使用 ffmpeg 的 thumbnail 滤镜自动选择有代表性的帧
            # -vf "thumbnail,scale=..." 组合使用
            cmd = [
                ffmpeg_path,
                '-i', source_path,
                '-vf', f'thumbnail,scale={max_size}:{max_size}:force_original_aspect_ratio=decrease',
                '-frames:v', '1',
                '-y',  # 覆盖已存在的文件
                thumb_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding=encoding, errors=errors)
            
            if result.returncode == 0:
                logger.info(f"Generated video thumbnail: {thumb_path}")
                return True
            else:
                logger.error(f"ffmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout generating video thumbnail for: {source_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to generate video thumbnail: {str(e)}")
            return False
    
    @staticmethod
    def generate_gif_thumbnail(source_path: str, thumb_path: str, ffmpeg_path: str, max_size: int = 300) -> bool:
        """使用 ffmpeg 为 GIF 生成动态缩略图
        
        Args:
            source_path: 源GIF文件路径
            thumb_path: 缩略图输出路径
            ffmpeg_path: ffmpeg 可执行文件路径
            max_size: 缩略图最大尺寸
        """
        try:
            from PIL import Image
            
            # 在Windows上处理编码问题
            encoding = 'utf-8' if sys.platform != 'win32' else 'utf-8'
            errors = 'ignore' if sys.platform == 'win32' else 'strict'
            
            # 检查 GIF 尺寸
            with Image.open(source_path) as img:
                width, height = img.size
            
            # 只有超过 max_size 才需要缩放
            if width > max_size or height > max_size:
                if width > height:
                    scale_filter = f'scale={max_size}:-1'
                else:
                    scale_filter = f'scale=-1:{max_size}'
                
                cmd = [
                    ffmpeg_path,
                    '-i', source_path,
                    '-loop', '0',
                    '-vf', scale_filter,
                    '-y',
                    thumb_path
                ]
            else:
                # 不需要缩放，只转换格式
                cmd = [
                    ffmpeg_path,
                    '-i', source_path,
                    '-loop', '0',
                    '-y',
                    thumb_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding=encoding, errors=errors)
            
            if result.returncode == 0:
                logger.info(f"Generated gif thumbnail: {thumb_path}")
                return True
            else:
                logger.error(f"ffmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout generating gif thumbnail for: {source_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to generate gif thumbnail: {str(e)}")
            return False

    @staticmethod
    def generate_thumbnail(
        source_path: str,
        thumb_path: str,
        media_type: str,
        ffmpeg_path: str,
        max_size: int = 300
    ) -> bool:
        """为媒体生成缩略图
        
        Args:
            source_path: 源文件路径
            thumb_path: 缩略图保存路径
            media_type: 媒体类型 ("VIDEO"/"IMAGE")
            ffmpeg_path: ffmpeg 可执行文件路径
            max_size: 缩略图最大边长（默认300像素）
        
        Returns:
            是否生成成功
        """
        try:
            if media_type == "VIDEO":
                # 视频：使用 ffmpeg 提取帧并生成缩略图
                return ThumbnailUtils.generate_video_thumbnail(source_path, thumb_path, ffmpeg_path, max_size)
            else:
                # 图片：根据格式选择处理方式
                ext = os.path.splitext(source_path)[1].lower()
                if ext == ".gif":
                    # GIF：使用 ffmpeg 保持动画
                    return ThumbnailUtils.generate_gif_thumbnail(source_path, thumb_path, ffmpeg_path, max_size)
                else:
                    # 普通图片：使用 PIL
                    return ThumbnailUtils.generate_image_thumbnail(source_path, thumb_path, max_size)
                    
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {source_path}: {str(e)}")
            return False


class MediaInfoUtils:
    """媒体信息获取工具类"""
    
    @staticmethod
    def get_media_info(file_path: str, media_type: str, ffprobe_path: str = None) -> dict:
        """
        获取媒体的详细信息
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型 ("VIDEO" 或 "IMAGE")
            ffprobe_path: ffprobe 可执行文件路径（视频需要）
        
        Returns:
            包含媒体信息的字典，包括 width, height, duration
        """
        info = {
            "width": None,
            "height": None,
            "duration": None
        }
        
        if media_type == "VIDEO" and ffprobe_path:
            # 使用 ffprobe 获取视频属性
            try:
                import subprocess
                import json
                import sys
                
                encoding = 'utf-8' if sys.platform != 'win32' else 'utf-8'
                errors = 'ignore' if sys.platform == 'win32' else 'strict'
                
                result = subprocess.run(
                    [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path],
                    capture_output=True, text=True, timeout=10, encoding=encoding, errors=errors
                )
                
                if result.returncode == 0 and result.stdout:
                    data = json.loads(result.stdout)
                    streams = data.get('streams', [])
                    for stream in streams:
                        if stream.get('codec_type') == 'video':
                            info["width"] = stream.get('width')
                            info["height"] = stream.get('height')
                            break
                    format_data = data.get('format', {})
                    if format_data.get('duration'):
                        info["duration"] = int(float(format_data.get('duration', 0)))
            except Exception as e:
                logger.error(f"Failed to get video properties for {file_path}: {e}")
                
        elif media_type == "IMAGE":
            # 使用 PIL 获取图片属性
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    info["width"], info["height"] = img.size
            except Exception as e:
                logger.error(f"Failed to get image properties for {file_path}: {e}")
        
        return info
