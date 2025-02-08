
# Infraestructura de Almacenamiento

Como almacenamiento para los datos del proyecto hacemos uso de S3 en AWS, los recursos necesarios son provisionados y configurados haciendo uso de AWS CDK, una herramienta de Infraestructura como código que permite desplegar y administrar recursos en esta plataforma usando un CLI y definirla en un lenguaje de programación de alto nivel.

## Despliegue

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

## Configuración DVC

Una vez se despliegue el bucker y el usuario para utilizarlo, puede configurar su ambiente para usar las credenciales de dicho usuario.

> Para usar DVC con S3, primero [instalar el CLI de AWS](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). 

Desde la cuenta en la que creó el usuario en AWS para acceder al bucket de S3, genere unas llaves de acceso para configurar las credenciales en su ambiente local.

> [!NOTE]
> El uso de la cadena `cloud_remote` en los siguientes comandos hace referencia al nombre con el que se configuró el remoto de dvc en el proyecto.

Puede agregar estas credenciales a su archivo de credenciales de AWS, el cuál típicamente se encuentra en `~/.aws/credentials` 

```
[dvc]
aws_access_key_id = ...
aws_secret_access_key = ...
```

Y luego indicarle a dvc que use estas credenciales con los siguientes comandos:

```
$ dvc remote modify --local cloud_remote \
                    credentialpath 'path/to/credentials'
$ dvc remote modify cloud_remote profile 'dvc'
```

O bien, configurar directamente dvc con su access_key y su secret_access_key

```
$ dvc remote modify --local cloud_remote \
                    access_key_id 'mysecret'
$ dvc remote modify --local cloud_remote \
                    secret_access_key 'mysecret'
```

Luego de completar estos pasos está listo para descargar el archivo de datos con `dvc push`