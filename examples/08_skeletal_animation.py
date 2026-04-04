"""骨骼动画演示 - 骑士的idle/walk/attack/jump/hit全套动画"""

from gclub_pixel import CharacterBody, SkeletalAnimation

# 创建64px骑士
knight = CharacterBody(64)
knight.set_skin((220, 185, 145))
knight.set_hair("short", (130, 90, 45))
knight.set_armor("plate", (170, 175, 190))
knight.set_eyes((40, 55, 90))

# ===== 全套动画 =====

# 1. Idle呼吸 (6帧)
sa = SkeletalAnimation(knight, fps=6)
sa.idle(frames=6, amplitude=1)
sa.export_gif("output/anim_idle.gif", scale=4)
sa.export_spritesheet("output/anim_idle_sheet.png", scale=3)
print("idle: 6帧呼吸动画 ✓")

# 2. Walk走路 (8帧)
sa2 = SkeletalAnimation(knight, fps=8)
sa2.walk(frames=8, stride=2, bob=1)
sa2.export_gif("output/anim_walk.gif", scale=4)
sa2.export_spritesheet("output/anim_walk_sheet.png", scale=3)
print("walk: 8帧走路动画 ✓")

# 3. Attack攻击 (8帧, 有预备-出击-回收)
sa3 = SkeletalAnimation(knight, fps=10)
sa3.attack(frames=8)
sa3.export_gif("output/anim_attack.gif", scale=4)
sa3.export_spritesheet("output/anim_attack_sheet.png", scale=3)
print("attack: 8帧攻击动画 (anticipation → strike → follow-through) ✓")

# 4. Jump跳跃 (10帧, 有蹲下-起跳-滞空-落地)
sa4 = SkeletalAnimation(knight, fps=10)
sa4.jump(frames=10, height=6)
sa4.export_gif("output/anim_jump.gif", scale=4)
sa4.export_spritesheet("output/anim_jump_sheet.png", scale=3)
print("jump: 10帧跳跃动画 (squash → stretch → land) ✓")

# 5. Hit受击 (6帧, 有击退+闪白)
sa5 = SkeletalAnimation(knight, fps=10)
sa5.hit(frames=6)
sa5.export_gif("output/anim_hit.gif", scale=4)
sa5.export_spritesheet("output/anim_hit_sheet.png", scale=3)
print("hit: 6帧受击动画 (knockback + flash) ✓")

print("\n=== 骨骼动画套装生成完毕 ===")
print("  动画原理: anticipation / squash-stretch / follow-through / overlap")
print("  所有动画: idle / walk / attack / jump / hit")
