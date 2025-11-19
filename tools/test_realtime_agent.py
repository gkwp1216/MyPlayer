"""
실시간 RL 에이전트 테스트
학습된 모델의 플레이를 확인하고 통계를 수집
"""
import sys
from pathlib import Path
import time
import numpy as np
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

from stable_baselines3 import PPO
from src.rl_env_realtime import RealtimeGameEnv


def test_agent(model_path, num_episodes=5, max_steps_per_episode=1000):
    """학습된 에이전트 테스트"""
    
    print("=" * 60)
    print("🤖 실시간 RL 에이전트 테스ト")
    print("=" * 60)
    print(f"모델: {model_path}")
    print(f"테스트 에피소드: {num_episodes}")
    print(f"최대 스텝/에피소드: {max_steps_per_episode}")
    print("=" * 60)
    
    # 환경 생성
    env = RealtimeGameEnv(game="ML")
    
    # 모델 로드
    print("\n📦 모델 로딩 중...")
    model = PPO.load(model_path)
    print("✅ 모델 로드 완료!")
    
    # 통계 수집
    all_rewards = []
    all_lengths = []
    action_counts = {i: 0 for i in range(11)}
    
    print("\n⏰ 5초 후 테스트 시작...")
    print("⚠️  게임이 실행 중이어야 합니다!")
    print("⚠️  ESC 키로 언제든 중지 가능\n")
    
    for i in range(5, 0, -1):
        print(f"   {i}초...")
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🚀 테스트 시작!")
    print("=" * 60 + "\n")
    
    try:
        for episode in range(num_episodes):
            obs, info = env.reset()
            episode_reward = 0
            episode_length = 0
            
            print(f"\n📍 에피소드 {episode + 1}/{num_episodes}")
            print("-" * 60)
            
            for step in range(max_steps_per_episode):
                # ESC로 중지
                if keyboard.is_pressed('esc'):
                    print("\n⏹️  ESC 감지 - 테스트 중지")
                    raise KeyboardInterrupt
                
                # 행동 예측
                action, _states = model.predict(obs, deterministic=True)
                action_counts[int(action)] += 1
                
                # 행동 실행
                obs, reward, done, truncated, info = env.step(action)
                
                episode_reward += reward
                episode_length += 1
                
                # 주요 이벤트 출력
                if reward > 1.0:
                    action_name = get_action_name(int(action))
                    print(f"  Step {step+1:4d} | Action: {action_name:15s} | Reward: {reward:+.2f} ⭐")
                
                if done or truncated:
                    break
            
            all_rewards.append(episode_reward)
            all_lengths.append(episode_length)
            
            print(f"\n📊 에피소드 {episode + 1} 결과:")
            print(f"   총 보상: {episode_reward:.2f}")
            print(f"   스텝 수: {episode_length}")
            print(f"   평균 보상/스텝: {episode_reward/episode_length:.3f}")
    
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지됨")
    
    finally:
        env.close()
    
    # 최종 통계
    if all_rewards:
        print("\n" + "=" * 60)
        print("📈 최종 통계")
        print("=" * 60)
        print(f"평균 보상: {np.mean(all_rewards):.2f} (±{np.std(all_rewards):.2f})")
        print(f"최고 보상: {np.max(all_rewards):.2f}")
        print(f"최저 보상: {np.min(all_rewards):.2f}")
        print(f"평균 에피소드 길이: {np.mean(all_lengths):.0f} 스텝")
        
        print("\n🎯 행동 분포:")
        total_actions = sum(action_counts.values())
        for action_id in sorted(action_counts.keys()):
            count = action_counts[action_id]
            percentage = (count / total_actions * 100) if total_actions > 0 else 0
            action_name = get_action_name(action_id)
            bar = "█" * int(percentage / 2)
            print(f"  {action_name:15s}: {count:5d} ({percentage:5.1f}%) {bar}")
        
        print("\n" + "=" * 60)


def get_action_name(action):
    """행동 ID -> 이름"""
    action_names = {
        0: "Idle",
        1: "Left",
        2: "Right",
        3: "Teleport",
        4: "Attack",
        5: "Buff(D)",
        6: "Buff(Shift)",
        7: "Buff(Alt)",
        8: "Up[차단]",
        9: "Down[차단]",
        10: "Summon(Home)"
    }
    return action_names.get(action, f"Unknown({action})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="실시간 RL 에이전트 테스트")
    parser.add_argument(
        "--model",
        type=str,
        default="models/realtime/ML/ML_ppo_realtime_final.zip",
        help="테스트할 모델 경로"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="테스트 에피소드 수"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1000,
        help="에피소드당 최대 스텝 수"
    )
    
    args = parser.parse_args()
    
    test_agent(args.model, args.episodes, args.steps)
