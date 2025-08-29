import tkinter as tk
from tkinter import ttk, messagebox
import random


class BubbleSortApp:
    def __init__(self, master):
        self.master = master
        master.title("冒泡排序演示")
        self.steps = []
        self.current_step = 0
        self.after_id = None
        self.animating = False  # 动画进行中标志
        self.elements = []  # 存储画布元素引用
        self.animation_frames = 20  # 动画帧数
        self.awaiting_swap = False  # 手动模式下：已高亮、等待用户确认交换

        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 控制面板
        control_frame = ttk.Frame(self.master, padding=10)
        control_frame.grid(row=0, column=0, sticky=tk.N)

        # 数字输入
        ttk.Label(control_frame, text="数字数量:").grid(row=0, column=0, sticky=tk.W)
        self.num_entry = ttk.Entry(control_frame, width=5)
        self.num_entry.grid(row=0, column=1, sticky=tk.W)

        # 排序方式
        self.sort_order = tk.StringVar(value="ascending")
        ttk.Radiobutton(control_frame, text="升序", variable=self.sort_order, value="ascending").grid(row=1, column=0,
                                                                                                      columnspan=2,
                                                                                                      sticky=tk.W)
        ttk.Radiobutton(control_frame, text="降序", variable=self.sort_order, value="descending").grid(row=2, column=0,
                                                                                                       columnspan=2,
                                                                                                       sticky=tk.W)

        # 演示模式
        self.demo_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(control_frame, text="自动演示", variable=self.demo_mode, value="auto").grid(row=3, column=0,
                                                                                                    columnspan=2,
                                                                                                    sticky=tk.W)
        ttk.Radiobutton(control_frame, text="手动演示", variable=self.demo_mode, value="manual").grid(row=4, column=0,
                                                                                                      columnspan=2,
                                                                                                      sticky=tk.W)

        # 开始按钮
        ttk.Button(control_frame, text="开始排序", command=self.start_sorting).grid(row=5, column=0, columnspan=2,
                                                                                    pady=5)

        # 手动控制按钮
        self.manual_controls = ttk.Frame(control_frame)
        ttk.Button(self.manual_controls, text="上一步", command=self.prev_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls, text="下一步", command=self.next_step).pack(side=tk.LEFT, padx=2)

        # 画布用于可视化
        self.canvas = tk.Canvas(self.master, width=800, height=200, bg="white")
        self.canvas.grid(row=0, column=1, padx=10, pady=10)

    # 统一取消挂起的 after 调度（防护）
    def cancel_after(self):
        if self.after_id:
            try:
                self.master.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def start_sorting(self):
        # 验证输入
        try:
            num = int(self.num_entry.get())
            if num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的正整数")
            return

        # 生成随机数组和步骤
        arr = random.sample(range(1, 100), num)
        self.steps = self.generate_steps(arr, self.sort_order.get() == "ascending")
        self.current_step = 0
        self.awaiting_swap = False

        # 清除之前的动画/调度
        self.cancel_after()

        # 处理演示模式
        if self.demo_mode.get() == "auto":
            self.manual_controls.grid_remove()
            self.auto_step()
        else:
            self.manual_controls.grid(row=6, column=0, columnspan=2, pady=5)
            self.show_step()

    def generate_steps(self, arr, ascending):
        steps = []
        arr = arr.copy()
        n = len(arr)

        steps.append({"array": arr.copy(), "compared": None, "swap": False})

        for i in range(n - 1):
            swapped = False
            for j in range(n - i - 1):
                compared = (j, j + 1)

                if (ascending and arr[j] > arr[j + 1]) or (not ascending and arr[j] < arr[j + 1]):
                    # 记录：先比较（将被标为需要交换），再记录交换位置供动画使用
                    steps.append({
                        "array": arr.copy(),
                        "compared": compared,
                        "swap": True,
                        "swap_positions": (j, j + 1)
                    })
                    # 做实际交换（用于后续步骤的数组状态）
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swapped = True
                else:
                    # 记录：比较但不交换（符合顺序）
                    steps.append({
                        "array": arr.copy(),
                        "compared": compared,
                        "swap": False
                    })

            if not swapped:
                break

        steps.append({"array": arr.copy(), "compared": None, "swap": False})
        return steps

    def show_step(self):
        if self.animating:  # 防止动画期间被中断
            return

        # 清画布并初始化元素列表
        self.canvas.delete("all")
        self.elements = []
        # 注意：不要无条件清 awaiting_swap，这里在需要时才复位

        if self.current_step >= len(self.steps):
            return

        step = self.steps[self.current_step]
        arr = step["array"]

        # 初始化所有元素的位置
        x_start = 50
        y = 100
        width = 40
        height = 40
        spacing = 10

        for i, num in enumerate(arr):
            x = x_start + i * (width + spacing)
            rect = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill="white", outline="black"
            )
            text = self.canvas.create_text(
                x + width / 2, y + height / 2,
                text=str(num), font=("Arial", 14)
            )
            self.elements.append({
                "rect": rect,
                "text": text,
                "x": x,
                "y": y
            })

        # 如果是交换步骤
        if step.get("swap_positions"):
            # 自动模式：先高亮（黄色），短暂停留后再做交换动画
            if self.demo_mode.get() == "auto":
                self.highlight_elements(step["compared"], True)
                swap_pos = step["swap_positions"]
                # 延迟启动动画（自动），并保存 after_id
                self.cancel_after()
                self.after_id = self.master.after(500, lambda pos=swap_pos: self.animate_swap(pos))
            else:
                # 手动模式：只高亮（等待用户点击“下一步”确认交换）
                # 设置 awaiting_swap=True 表示当前显示的是“等待用户确认交换”的状态
                self.highlight_elements(step["compared"], True)
                self.awaiting_swap = True
        else:
            # 普通比较步骤（如果符合顺序则显示绿色）
            # 在进入一个新的非交换步骤时，确保等待标志复位（此时步进应该由用户触发）
            self.awaiting_swap = False
            self.highlight_elements(step["compared"], step["swap"])
            # 如果存在之前的挂起 after，手动模式下应取消它（以防万一）
            if self.demo_mode.get() == "manual":
                self.cancel_after()

    def auto_step(self):
        # 如果正在动画，先不做任何事
        if self.animating:
            return

        # 如果已展示完所有步骤，退出
        if self.current_step >= len(self.steps):
            return

        # 确保仍处于自动模式
        if self.demo_mode.get() != "auto":
            return

        step = self.steps[self.current_step]
        # 显示当前步骤（如果是交换步骤，show_step 会启动延迟动画）
        self.show_step()
        # 对于非交换步骤，直接推进并安排下一次（仅在仍为自动模式时）
        if not step.get("swap_positions"):
            self.current_step += 1
            if self.current_step < len(self.steps) and self.demo_mode.get() == "auto":
                # 先取消已有的 after，避免重复
                self.cancel_after()
                self.after_id = self.master.after(1000, self.auto_step)

    def next_step(self):
        # 在任何手动交互之前，取消可能存在的挂起 after（避免残留 auto 调度）
        self.cancel_after()

        # 如果动画正在进行或已有等待交换的动画不能被打断
        if self.animating:
            return

        # 如果当前处于等待用户确认交换（手动模式），这次“下一步”应启动交换动画，而不是推进到下一步
        if self.awaiting_swap:
            step = self.steps[self.current_step]
            pos = step.get("swap_positions")
            if pos:
                # 清除等待标志并开始动画
                self.awaiting_swap = False
                self.animate_swap(pos)
            return

        # 否则前进一步并展示（只在未到最后一步时）
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.show_step()

    def prev_step(self):
        # 在任何手动交互之前，取消可能存在的挂起 after（避免残留 auto 调度）
        self.cancel_after()

        if self.animating:
            return
        # 取消任何等待交换状态
        self.awaiting_swap = False
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()

    def animate_swap(self, positions):
        # positions 是交换前的索引 (i, j)
        self.animating = True
        self.awaiting_swap = False  # 启动动画时取消等待标志（以免再次触发）
        # 在启动动画前取消任何挂起的 after（防护）
        self.cancel_after()

        i, j = positions
        # 防护：如果索引超界直接结束
        if i < 0 or j < 0 or i >= len(self.elements) or j >= len(self.elements):
            self.animating = False
            return

        elem1 = self.elements[i]
        elem2 = self.elements[j]

        # 计算移动参数
        start_x1 = elem1["x"]
        start_x2 = elem2["x"]
        target_x1 = start_x2
        target_x2 = start_x1
        dx1 = (target_x1 - start_x1) / self.animation_frames
        dx2 = (target_x2 - start_x2) / self.animation_frames

        # 保存动画参数（包含原索引 i,j 和目标 x，便于在动画结束时同步 self.elements）
        self.animation_params = {
            "current_frame": 0,
            "elem1": elem1,
            "elem2": elem2,
            "dx1": dx1,
            "dx2": dx2,
            "start_x1": start_x1,
            "start_x2": start_x2,
            "target_x1": target_x1,
            "target_x2": target_x2,
            "i": i,
            "j": j
        }

        self.do_animation_frame()

    def do_animation_frame(self):
        params = self.animation_params

        # 动画完成条件
        if params["current_frame"] >= self.animation_frames:
            # 动画结束后：我们统一使用下一步的数据重新重画画布，避免残留移动状态造成后续跳步
            # 先取消任何挂起的 after
            self.cancel_after()

            # 将动画状态标记为结束
            self.animating = False
            # 清除高亮（暂时）
            self.clear_highlights()

            # 推进步数（动画表示的交换步骤完成）
            self.current_step += 1

            # 重新用当前步骤数据完整重绘（重要：保证显示严格跟随 steps 的 array）
            # 注意：这在手动模式下不会自动继续，只是把画面刷新到交换完成后的状态
            self.show_step()

            # 如果仍处于自动模式并且未结束，则安排下一次自动播放
            if self.demo_mode.get() == "auto" and self.current_step < len(self.steps):
                self.cancel_after()
                self.after_id = self.master.after(1000, self.auto_step)
            return

        # 每帧更新位置
        dx1 = params["dx1"]
        dx2 = params["dx2"]
        elem1 = params["elem1"]
        elem2 = params["elem2"]

        self.canvas.move(elem1["rect"], dx1, 0)
        self.canvas.move(elem1["text"], dx1, 0)
        self.canvas.move(elem2["rect"], dx2, 0)
        self.canvas.move(elem2["text"], dx2, 0)

        params["current_frame"] += 1
        # 20ms 后继续下一帧
        self.cancel_after()
        self.after_id = self.master.after(20, self.do_animation_frame)

    def highlight_elements(self, compared, swap):
        """
        compared: tuple 或 None
        swap: 布尔 - 表示这次比较是否需要交换（True 表示要交换 -> 显示黄色）
                                            （False 表示不需要交换 -> 显示绿色）
        """
        # 先把所有恢复为白色（方便刷新）
        for e in self.elements:
            self.canvas.itemconfig(e["rect"], fill="white")

        if compared:
            for i in compared:
                # 正确顺序（不交换）显示绿色；需要交换的显示黄色
                color = "lightgreen" if not swap else "yellow"
                # 防护：索引越界检查
                if 0 <= i < len(self.elements):
                    self.canvas.itemconfig(self.elements[i]["rect"], fill=color)

    def clear_highlights(self):
        for e in self.elements:
            self.canvas.itemconfig(e["rect"], fill="white")


if __name__ == "__main__":
    root = tk.Tk()
    app = BubbleSortApp(root)
    root.mainloop()
