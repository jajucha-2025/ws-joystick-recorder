try:
    import jchm
except ModuleNotFoundError:
    pass
import cv2
import os
from enum import IntEnum
from typing import Callable
import numpy

class CameraMode(IntEnum):
    JAJUCHA = 0 # 자주차
    COMPUTER = 1 # 컴퓨터

class Camera:
    def __init__(self, mode: CameraMode, device):
        if not isinstance(mode, CameraMode):
            raise TypeError(f"mode는 CameraMode여야 합니다. got {type(mode).__name__}")
        self.mode = mode

        try:
            if mode is CameraMode.JAJUCHA: # 자주차 카메라
                try:
                    self.camera = jchm.camera
                except NameError as e: # jchm가 정의되지 않았다면 (임포트되지 않았다면) NameError
                    raise ImportError("jchm 모듈을 사용할 수 없습니다.") from e
                self.set_camera_device(device)
                self.getFrame: Callable[[], numpy.ndarray] = self.__getJajuchaFrame
                self.showFrame: Callable[[numpy.ndarray, int], None] = self.__showFrameOnJajucha

            elif mode is CameraMode.COMPUTER: # 로컬 컴퓨터 웹캠
                self.set_camera_device(device)
                if not self.camera.isOpened():
                    raise RuntimeError(f"카메라를 인식할 수 없습니다. (index {self.device})")
                self.getFrame = self.__getComputerFrame
                self.showFrame = self.__showFrameOnComputer

            else:
                raise ValueError(f"사용불가한 mode: {mode}")

        except Exception as e: # init 전반의 예외를 포장
            raise RuntimeError("카메라 초기화 도중 예기치 않은 오류가 발생했습니다.") from e

    # --- public helpers ---

    def set_camera_device(self, new_device) -> None:
        """카메라 변경"""
        if self.mode is CameraMode.JAJUCHA:
            if type(new_device) is not str:
                raise TypeError("자주차 카메라의 디바이스 이름은 문자열이여야 합니다.")
            self.device = new_device
            self.camera = jchm.camera
        elif self.mode is CameraMode.COMPUTER:
            if type(new_device) is not int:
                raise TypeError("컴퓨터 카메라의 디바이스 이름은 정수여야 합니다.")
            if hasattr(self, "camera") and self.camera is not None:
                self.release()
            self.device = new_device
            self.camera = cv2.VideoCapture(new_device)

    def release(self) -> None:
        """컴퓨터 모드일 때 리소스 정리"""
        if self.mode is CameraMode.COMPUTER and hasattr(self, "camera") and self.camera is not None:
            self.camera.release()
            # 창 사용했다면 닫기
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
    
    def saveFrame(self, mat, output_dir: str, filename: str, jpg_compress_quality: int):
        if not os.path.exists(output_dir):
            raise NotADirectoryError("output 디렉토리를 찾지 못했습니다.")
        img_path = os.path.join(output_dir, filename)
        cv2.imwrite(f"{img_path}", mat, [cv2.IMWRITE_JPEG_QUALITY, jpg_compress_quality])

    # --- JAJUCHA backend ---

    def __getJajuchaFrame(self):
        if self.device == "lidar":
            return self.camera.get_depth()
        return self.camera.get_image(self.device)

    def __showFrameOnJajucha(self, mat: numpy.ndarray, quality=80):
        self.camera.show_image(mat, self.device, quality)

    # --- COMPUTER backend ---

    def __getComputerFrame(self):
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError(f"카메라를 인식할 수 없습니다. (index {self.device})")
        return frame

    def __showFrameOnComputer(self, mat: numpy.ndarray, quality=100):
        new_w = int(mat.shape[1]/(quality/100))
        new_h = int(mat.shape[0]/(quality/100))
        resized = cv2.resize(mat, (new_w, new_h))
        cv2.imshow(str(self.device), resized)
