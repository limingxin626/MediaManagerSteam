import os
import datetime
import hashlib
import logging
import subprocess
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


def calculate_file_hash(file_path: str, size_threshold: int = 100 * 1024 * 1024) -> str | None:
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
        return None


class ThumbnailUtils:
    """缩略图生成工具类"""
    
    @staticmethod
    def generate_image_thumbnail(source_path: str, thumb_path: str, max_size: int = 300) -> bool:
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
        """使用 ffmpeg 为视频生成缩略图，thumbnail 滤镜失败时 fallback 到取第一帧

        Args:
            source_path: 源视频文件路径
            thumb_path: 缩略图输出路径
            ffmpeg_path: ffmpeg 可执行文件路径
            max_size: 缩略图最大尺寸
        """
        scale = f'scale={max_size}:{max_size}:force_original_aspect_ratio=decrease'
        # 优先用 thumbnail 滤镜选取代表帧
        cmd = [
            ffmpeg_path,
            '-i', source_path,
            '-vf', f'thumbnail,{scale}',
            '-frames:v', '1',
            '-y',
            thumb_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                    encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                logger.info(f"Generated video thumbnail: {thumb_path}")
                return True

            # fallback：取第一帧（适用于极短视频）
            logger.warning(f"thumbnail filter failed, falling back to first frame: {source_path}")
            cmd_fallback = [
                ffmpeg_path,
                '-i', source_path,
                '-vf', scale,
                '-frames:v', '1',
                '-y',
                thumb_path
            ]
            result = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=30,
                                    encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                logger.info(f"Generated video thumbnail (fallback): {thumb_path}")
                return True

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
        """使用 ffmpeg 为 GIF 生成动态 webp 缩略图

        Args:
            source_path: 源GIF文件路径
            thumb_path: 缩略图输出路径（.webp）
            ffmpeg_path: ffmpeg 可执行文件路径
            max_size: 缩略图最大尺寸
        """
        try:
            from PIL import Image

            # 检查 GIF 尺寸
            with Image.open(source_path) as img:
                width, height = img.size

            vf_filters = []
            # 只有超过 max_size 才需要缩放
            if width > max_size or height > max_size:
                if width > height:
                    vf_filters.append(f'scale={max_size}:-1')
                else:
                    vf_filters.append(f'scale=-1:{max_size}')

            cmd = [
                ffmpeg_path,
                '-i', source_path,
                '-c:v', 'libwebp_anim',
                '-loop', '0',
            ]
            if vf_filters:
                cmd += ['-vf', ','.join(vf_filters)]
            cmd += ['-y', thumb_path]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                    encoding='utf-8', errors='ignore')

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
    def _parse_ffprobe(file_path: str, ffprobe_path: str) -> dict | None:
        """调用 ffprobe 返回解析后的 JSON，失败返回 None"""
        import json
        try:
            result = subprocess.run(
                [ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', file_path],
                capture_output=True, text=True, timeout=10,
                encoding='utf-8', errors='ignore',
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"ffprobe failed for {file_path}: {e}")
        return None

    @staticmethod
    def _extract_exif_date(img) -> str | None:
        """从 PIL Image 提取 EXIF 拍摄日期，返回 ISO 格式字符串或 None"""
        try:
            exif = img.getexif()
            if not exif:
                return None
            # 36867 = DateTimeOriginal, 36868 = DateTimeDigitized, 306 = DateTime
            for tag_id in (36867, 36868, 306):
                val = exif.get(tag_id)
                if val:
                    # EXIF 格式: "2024:01:15 14:30:00" → "2024-01-15T14:30:00"
                    return val.replace(':', '-', 2).replace(' ', 'T', 1)
        except Exception as e:
            logger.debug(f"Failed to extract EXIF date: {e}")
        return None

    @staticmethod
    def _extract_exif_gps(img) -> dict | None:
        """从 PIL Image 提取 GPS 坐标，返回 {"lat": float, "lng": float} 或 None"""
        try:
            exif = img.getexif()
            if not exif:
                return None
            # GPS info 在 IFD 0x8825
            gps_ifd = exif.get_ifd(0x8825)
            if not gps_ifd:
                return None

            def _to_degrees(value):
                """将 EXIF GPS 元组 ((d,1),(m,1),(s,100)) 转为十进制度数"""
                d, m, s = value
                if isinstance(d, tuple):
                    d = d[0] / d[1]
                if isinstance(m, tuple):
                    m = m[0] / m[1]
                if isinstance(s, tuple):
                    s = s[0] / s[1]
                return float(d) + float(m) / 60 + float(s) / 3600

            # 2=GPSLatitude, 1=GPSLatitudeRef, 4=GPSLongitude, 3=GPSLongitudeRef
            lat_data = gps_ifd.get(2)
            lat_ref = gps_ifd.get(1, 'N')
            lng_data = gps_ifd.get(4)
            lng_ref = gps_ifd.get(3, 'E')

            if lat_data and lng_data:
                lat = _to_degrees(lat_data)
                lng = _to_degrees(lng_data)
                if lat_ref == 'S':
                    lat = -lat
                if lng_ref == 'W':
                    lng = -lng
                return {"lat": round(lat, 6), "lng": round(lng, 6)}
        except Exception as e:
            logger.debug(f"Failed to extract EXIF GPS: {e}")
        return None

    @staticmethod
    def get_media_info(file_path: str, media_type: str, ffprobe_path: str = None) -> dict:
        """
        获取媒体的详细信息

        Returns:
            dict with keys: width, height, duration, bitrate, fps, codec, has_audio, taken_at, gps
            当前只有 width/height/duration 会写入数据库，其余字段供将来使用。
        """
        info = {
            "width": None,
            "height": None,
            "duration": None,
            "bitrate": None,
            "fps": None,
            "codec": None,
            "has_audio": None,
            "taken_at": None,
            "gps": None,
        }

        ext = os.path.splitext(file_path)[1].lower()

        if media_type == "VIDEO" and ffprobe_path:
            data = MediaInfoUtils._parse_ffprobe(file_path, ffprobe_path)
            if data:
                has_audio = False
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video' and info["width"] is None:
                        info["width"] = stream.get('width')
                        info["height"] = stream.get('height')
                        info["codec"] = stream.get('codec_name')
                        # fps: r_frame_rate 格式为 "30/1" 或 "30000/1001"
                        r_frame_rate = stream.get('r_frame_rate', '')
                        if '/' in r_frame_rate:
                            num, den = r_frame_rate.split('/')
                            if int(den) > 0:
                                info["fps"] = round(int(num) / int(den), 2)
                    elif stream.get('codec_type') == 'audio':
                        has_audio = True
                info["has_audio"] = has_audio

                format_data = data.get('format', {})
                if format_data.get('duration'):
                    info["duration"] = round(float(format_data['duration']))
                if format_data.get('bit_rate'):
                    info["bitrate"] = int(format_data['bit_rate'])

                # 拍摄日期: format.tags.creation_time
                tags = format_data.get('tags', {})
                creation_time = tags.get('creation_time') or tags.get('Creation_time')
                if creation_time:
                    info["taken_at"] = creation_time

                # 地理位置: format.tags.location 格式 "+31.2345+121.4567/"
                location = tags.get('location') or tags.get('com.apple.quicktime.location.ISO6709')
                if location:
                    import re
                    m = re.match(r'([+-][\d.]+)([+-][\d.]+)', location)
                    if m:
                        info["gps"] = {
                            "lat": round(float(m.group(1)), 6),
                            "lng": round(float(m.group(2)), 6),
                        }

        elif media_type == "IMAGE":
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    info["width"], info["height"] = img.size

                    # EXIF 拍摄日期和 GPS (JPEG/TIFF 等有 EXIF 的格式)
                    info["taken_at"] = MediaInfoUtils._extract_exif_date(img)
                    info["gps"] = MediaInfoUtils._extract_exif_gps(img)

                    # GIF: 用 ffprobe 获取准确 duration，fallback 到 PIL 帧累加
                    if ext == '.gif':
                        info["codec"] = "gif"
                        if ffprobe_path:
                            data = MediaInfoUtils._parse_ffprobe(file_path, ffprobe_path)
                            if data:
                                fmt_dur = data.get('format', {}).get('duration')
                                if fmt_dur:
                                    info["duration"] = round(float(fmt_dur))
                        # fallback: PIL 帧累加
                        if info["duration"] is None and hasattr(img, 'n_frames') and img.n_frames > 1:
                            total_ms = 0
                            for frame_idx in range(img.n_frames):
                                img.seek(frame_idx)
                                total_ms += img.info.get('duration', 100)
                            info["duration"] = round(total_ms / 1000)
            except Exception as e:
                logger.error(f"Failed to get image properties for {file_path}: {e}")

        return info
