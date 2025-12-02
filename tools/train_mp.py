"""
MP 게임 전용 실시간 강화학습 학습 스크립트
메이플스토리 사냥을 플레이하면서 실시간으로 학습

사용법: py tools/train_mp.py --timesteps 50000
"""
import argparse
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from src.rl_env_mp import MPRealtimeEnv
import torch
import keyboard


class RealtimeTrainingCallback(BaseCallback):
    """실시간 학습 콜백"""
    
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []
        self.current_episode_reward = 0
        self.current_episode_length = 0
        
    def _on_step(self):
        """매 스텝마다 호출"""
        # ESC로 중지
        if keyboard.is_pressed('esc'):
            print("\n⏹️  ESC 감지 - 학습 중지")
            return False
        
        # 통계 수집
        self.current_episode_reward += self.locals['rewards'][0]
        self.current_episode_length += 1
        
        # 에피소드 종료 시
        if self.locals['dones'][0]:
            self.episode_rewards.append(self.current_episode_reward)
            self.episode_lengths.append(self.current_episode_length)
            
            # 최근 10 에피소드 평균
            if len(self.episode_rewards) >= 10:
                avg_reward = sum(self.episode_rewards[-10:]) / 10
                avg_length = sum(self.episode_lengths[-10:]) / 10
                
                print(f"\n📊 에피소드 {len(self.episode_rewards)}")
                print(f"   보상: {self.current_episode_reward:.2f}")
                print(f"   길이: {self.current_episode_length} 스텝")
                print(f"   평균 (최근 10): {avg_reward:.2f} 보상, {avg_length:.0f} 스텝")
            
            self.current_episode_reward = 0
            self.current_episode_length = 0
        
        return True


def main():
    parser = argparse.ArgumentParser(description="MP 게임 실시간 RL 학습")
    parser.add_argument("--timesteps", type=int, default=50000, help="학습 타임스텝")
    parser.add_argument("--learning-rate", type=float, default=0.0003, help="학습률")
    parser.add_argument("--frame-width", type=int, default=84, help="프레임 너비")
    parser.add_argument("--frame-height", type=int, default=84, help="프레임 높이")
    parser.add_argument("--frame-stack", type=int, default=4, help="프레임 스택")
    parser.add_argument("--frame-skip", type=int, default=4, help="프레임 스킵")
    parser.add_argument("--load-model", type=str, help="기존 모델 로드")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎮 MP 게임 실시간 강화학습 (메이플스토리)")
    print("=" * 60)
    print(f"타임스텝: {args.timesteps:,}")
    print(f"학습률: {args.learning_rate}")
    print(f"프레임 크기: {args.frame_width}x{args.frame_height}")
    print(f"프레임 스킵: {args.frame_skip}")
    print("=" * 60)
    
    # 준비 확인
    print("\n⚠️  실시간 학습 주의사항:")
    print("  1. 메이플스토리가 실행 중이어야 합니다")
    print("  2. 캐릭터가 안전한 사냥터에 있어야 합니다")
    print("  3. 마우스/키보드를 건드리지 마세요")
    print("  4. ROI 설정이 되어있어야 합니다 (py tools/setup_roi.py)")
    print("  5. ESC로 언제든 중지 가능")
    print()
    
    # ROI 설정 확인
    roi_path = Path("configs/roi_settings.json")
    if not roi_path.exists():
        print("❌ ROI 설정이 없습니다!")
        print("   먼저 'py tools/setup_roi.py' 를 실행하세요")
        return
    
    input("준비되면 엔터를 누르세요... ")
    
    print("\n⏰ 5초 후 학습 시작...")
    for i in range(5, 0, -1):
        print(f"   {i}초...")
        time.sleep(1)
    
    # MP 환경 생성
    print("\n📊 MP 환경 생성 중...")
    env = MPRealtimeEnv(
        frame_width=args.frame_width,
        frame_height=args.frame_height,
        frame_stack=args.frame_stack,
        frame_skip=args.frame_skip
    )
    
    print(f"✅ 환경 생성 완료")
    print(f"   관측 공간: {env.observation_space.shape}")
    print(f"   행동 공간: {env.action_space.n}개")
    
    # 모델 생성 또는 로드
    if args.load_model:
        print(f"\n📂 기존 모델 로드: {args.load_model}")
        model = PPO.load(args.load_model, env=env)
        print("✅ 모델 로드 완료 (계속 학습)")
    else:
        print("\n🤖 PPO 모델 생성 중...")
        
        policy_kwargs = dict(
            features_extractor_kwargs=dict(features_dim=512),
            net_arch=[512, 512]
        )
        
        model = PPO(
            "CnnPolicy",
            env,
            learning_rate=args.learning_rate,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.05,
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs=policy_kwargs,
            verbose=1,
            tensorboard_log="logs/realtime/MP"
        )
        print("✅ 모델 생성 완료")
    
    # 콜백 설정
    checkpoint_dir = Path("models/realtime/MP/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_callback = CheckpointCallback(
        save_freq=5000,
        save_path=str(checkpoint_dir),
        name_prefix="MP_ppo_realtime"
    )
    
    training_callback = RealtimeTrainingCallback(verbose=1)
    
    # 학습 시작
    print("\n🚀 학습 시작!")
    print("📊 TensorBoard 모니터링:")
    print("   tensorboard --logdir logs/realtime/MP")
    print("\n⏹️  ESC 키를 눌러 안전하게 중지")
    print("=" * 60)
    
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=[checkpoint_callback, training_callback],
            progress_bar=True
        )
    except KeyboardInterrupt:
        print("\n⏹️  학습 중단됨 (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
    finally:
        # 최종 모델 저장
        final_model_dir = Path("models/realtime/MP")
        final_model_dir.mkdir(parents=True, exist_ok=True)
        final_model_path = final_model_dir / "MP_ppo_realtime_final.zip"
        
        model.save(str(final_model_path))
        env.close()
        
        print("\n" + "=" * 60)
        print("✅ 학습 완료!")
        print(f"💾 모델 저장: {final_model_path}")
        print("=" * 60)
        
        if training_callback.episode_rewards:
            print(f"\n📈 학습 통계:")
            print(f"   총 에피소드: {len(training_callback.episode_rewards)}")
            print(f"   평균 보상: {sum(training_callback.episode_rewards) / len(training_callback.episode_rewards):.2f}")
            print(f"   최고 보상: {max(training_callback.episode_rewards):.2f}")
        
        print("\n🧪 테스트 방법:")
        print(f"   py tools/test_agent_gui.py")
        print(f"   → 모델 선택: {final_model_path}")


if __name__ == "__main__":
    main()
