import flet as ft
import math # 科学計算の数学モジュールをインポート


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1, data=None):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = data if data is not None else text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.Colors.WHITE24
        self.color = ft.Colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked, data=None):
        CalcButton.__init__(self, text, button_clicked, data=data)
        self.bgcolor = ft.Colors.ORANGE
        self.color = ft.Colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.color = ft.Colors.BLACK

    # 科学計算用のボタン
class ScientificButton(CalcButton):
    def __init__(self, text, button_clicked, data=None):
        CalcButton.__init__(self, text, button_clicked, data=data)
        self.bgcolor = ft.Colors.WHITE24  
        self.color = ft.Colors.WHITE 


class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        
        self.reset()

        self.result = ft.Text(value="0", color=ft.Colors.WHITE, size=30) 
        self.width = 600
        self.bgcolor = ft.Colors.BLACK
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.standard_buttons = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="÷", button_clicked=self.button_clicked, data="/"), 
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="×", button_clicked=self.button_clicked, data="*"), 
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        DigitButton(text="0", expand=2, button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )
        #科学計算のボタン
        self.scientific_buttons = ft.Column(
            controls=[
                ScientificButton(text="sin", button_clicked=self.button_clicked, data="sin"), # sinボタン
                ScientificButton(text="cos", button_clicked=self.button_clicked, data="cos"), # cosボタン
                ScientificButton(text="tan", button_clicked=self.button_clicked, data="tan"), # tanボタン
                ScientificButton(text="√x", button_clicked=self.button_clicked, data="sqrt"), # 平方根ボタン
                ScientificButton(text="xʸ", button_clicked=self.button_clicked, data="pow"), # 累乗ボタン
            ],
            spacing=10, 
            horizontal_alignment=ft.CrossAxisAlignment.START
        )

        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment="end", expand=True), 
                
                ft.Row(
                    controls=[
                        self.scientific_buttons, 
                        ft.VerticalDivider(width=1), 
                        self.standard_buttons, 
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True
                )
            ]
        )
        
    def button_clicked(self, e):
        data = e.control.data
        current_value = self.result.value 
        print(f"Button clicked with data = {data}")
        
        if current_value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()
            
        elif data in ("sin", "cos", "tan", "sqrt"):
            try:
                num = float(current_value)
                
                if data == "sin":
                    rad = math.radians(num)
                    self.result.value = self.format_number(math.sin(rad))
                elif data == "cos":
                    rad = math.radians(num)
                    self.result.value = self.format_number(math.cos(rad))
                elif data == "tan":
                    rad = math.radians(num)
                    if abs(math.cos(rad)) < 1e-10:
                        self.result.value = "Error"
                    else:
                        self.result.value = self.format_number(math.tan(rad))
                elif data == "sqrt":
                    if num < 0:
                        self.result.value = "Error" 
                    else:
                        self.result.value = self.format_number(math.sqrt(num))
                        
                self.reset()
            except (ValueError, OverflowError):
                self.result.value = "Error"
                
        elif data == "pow":
            self.result.value = self.calculate(self.operand1, float(current_value), self.operator)
            self.operator = "^" 
            if self.result.value == "Error":
                self.operand1 = 0
            else:
                self.operand1 = float(self.result.value)
            self.new_operand = True
        
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            if self.result.value == "0" or self.new_operand == True:
                if data == "." and "." in self.result.value and not self.new_operand:
                    pass
                else:
                    self.result.value = data
                    self.new_operand = False
            else:
                if data == "." and "." in self.result.value:
                    pass
                else:
                    self.result.value = self.result.value + data

        elif data in ("+", "-", "*", "/"):
            try:
                self.result.value = self.calculate(self.operand1, float(current_value), self.operator)
                self.operator = data
                if self.result.value == "Error":
                    self.operand1 = 0
                else:
                    self.operand1 = float(self.result.value)
                self.new_operand = True
            except ValueError:
                 self.result.value = "Error"

        elif data in ("="):
            self.result.value = self.calculate(self.operand1, float(current_value), self.operator)
            self.reset()

        elif data in ("%"):
            try:
                self.result.value = self.format_number(float(current_value) / 100)
                self.reset()
            except ValueError:
                 self.result.value = "Error"

        elif data in ("+/-"):
            try:
                num = float(current_value)
                self.result.value = str(self.format_number(-num))
                self.new_operand = False
            except ValueError:
                 self.result.value = "Error"

        self.update()

    def format_number(self, num):
        if num == "Error":
            return num
        
        rounded_num = round(num, 10) 
        
        if rounded_num % 1 == 0:
            return int(rounded_num)
        else:
            return rounded_num

    def calculate(self, operand1, operand2, operator):

        if operator == "+":
            return self.format_number(operand1 + operand2)

        elif operator == "-":
            return self.format_number(operand1 - operand2)

        elif operator == "*":
            return self.format_number(operand1 * operand2)

        elif operator == "/":
            if operand2 == 0:
                return "Error"
            else:
                return self.format_number(operand1 / operand2)
                
        elif operator == "^":
            try:
                return self.format_number(math.pow(operand1, operand2))
            except OverflowError:
                 return "Error" 
        
        return self.format_number(operand2)

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "Scientific Calculator (Wide Layout)"
    page.window_width = 650
    page.window_height = 550
    calc = CalculatorApp()
    page.add(calc)
if __name__ == '__main__':
    ft.app(target=main)