"""while True:   
    num1=int(input("digita tu primer numero:  "))
    num2=int(input("digita tu segundo numero:  "))
    num3=int(input("digita tu tercer numero:  "))
    if num1 > num2 and num1 > num3:
        print(f"el numero mayor de los tres es:{num1}")
        break
    if num2 > num1 and num2 > num3:
        print(f"el numero mayor de los tres es {num2}")
        break
    else:
        print(f"el numero mayor de los tres es {num3}")
        break"""

"""numero=int(input("digita un numero \n"))
for i in range(1,10+1):
    resultado=numero * i
    print(f"{numero} * {i}= {resultado}")

for i in range(0,100):
    resultado= i + 1
    print(resultado)"""

"""contador=0
while True:
    numero=int(input("digita un numero (que no sea cero >:c\n"))
    if numero == 0:
        print(f"error, el numero que colocaste es 0\nla suma total es {contador}")
        break
    else:
        contador = contador + numero"""

numeroSecreto = 67
while True:
    numero=int(input("digita tu numero\n"))
    if numero == numeroSecreto:
        print(f"correcto, el numero secreto era {numeroSecreto}\nSIIIIX SEEEEVEEEEN")
        break
    elif numero >39 and numero < numeroSecreto:
        print("es un poquito mas alto")
    elif numero >numeroSecreto and numero < 72:
        print("te pasaste solo un poquito")
    elif numero <= 38:
        print("no, muy bajo")
    else:
        print("no, muy alto")