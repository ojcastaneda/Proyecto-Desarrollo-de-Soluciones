
# Infraestructura de Almacenamiento

Como almacenamiento para los datos del proyecto hacemos uso de S3 en AWS, los recursos necesarios son provisionados y configurados haciendo uso de AWS CDK, una herramienta de Infraestructura como código que permite desplegar y administrar recursos en esta plataforma usando un CLI y definirla en un lenguaje de programación de alto nivel.


<details>

<summary> Detalles sobre el provisionamiento </summary>

### Provisionamiento de Bucket y Usuario para DVC con CDK

Si desea replicar el provisionamiento del bucket y el usuario con el AWS CDK para utlizar DVC, primero debe contar con algunos prerequisitos:
1. Acceso a una cuenta de AWS con permisos para crear recursos
2. Instalación del CLI de AWS
3. Instalación node.js
4. Instalación de python, pip y virtualenv

Una vez se cuente con dichos prerequisitos, la documentación recomienda instalar el CLI de AWS CDK de manera global con el npm, el manejador de paquetes de node.js con el siguiente comando:

```
npm install -g aws-cdk
```

Luego, ubicado en la carpeta `./storage_infrastructure` del proyecto, necesita el siguiente comando para desplegar una serie de recursos en su cuenta de AWS que soportan el CDK. Por defecto se utilizarán las credenciales configuradas en el perfil `default` para el CLI de AWS.

```
cdk bootstrap
```

Puede probar la generación del Stack de CloudFormation (el servicio de Infraestructura como Código de AWS que usa el CDK internamente para desplegar los recursos) con el siguiente comando, que imprime la definición de esta infraestructura en la terminal

```
cdk synth
```

Finalmente, para desplegar esta infraestructura haga uso del siguiente comando:

```
cdk deploy
```

Es posible que en la terminal se le solicite confirmación para desplegar estos recursos ya que incluyen permisos sobre los mismos.

Otro beneficio de la infraestructura como código es que facilita eliminar los recursos que se provisionan en este stack con el siguiente comando.

```
cdk destroy
```

</details>