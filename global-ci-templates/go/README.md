# Golang
Acá encontrarás las definiciones por default para los CI para compilar y desplegar proyectos hechos en golang. Este es un trabajo colaborativo de los equipos DevOps/ApiCore. 
Ante cualquier duda o sugerencia, por favor contactarnos a través del canal de Slack **#gitlab-openshift**.

### Steps
El pipeline actual consiste de:
- Build/package
- Test: Realiza ejecuciones de tests unitarios, de integración, corre los tests unitarios con el detector de data races (`go test -race`). También prepara los artifacts de reportes para sonarqube
- Quality: Realiza los escaneos de sonarqube y golangci-lint
- Deploy

Estos steps se ejecutan siempre que se puedan con un Gitlab Runner tipo BASH DOCKER. 

    
### Ejemplos

A fines prácticos, se agrega abajo un ejemplo importando los archivos de este proyecto desde cualquier otro:

__.gitlab-ci.yml__
```yaml
include:
  - project: 'santander-tecnologia/global-ci-templates'
    file: 'go/.gitlab-ci.yml'
    ref: 'feature.go'
  - local: '.ci-variables.yml'
```

Como se observa, también se importa un archivo local, llamado ".ci-variables.yml". Este archivo existe para que, en caso de querer agregar variables, se puedan agregar al mismo, en vez de 'ensuciar' el `.gitlab-ci.yml`. A tener en cuenta, todas las variables definidas en ese archivo tienen menor prioridad que las definidas por los templates, por lo que no pisarán los valores ya establecidos. 
Si hubiera necesidad de hacerlo, por favor contactarse con el equipo de DevOps para analizar la necesidad. 

### Estructura de proyecto

Como requerimiento único especifico de go, el pipeline espera un `package main` con su respectivo archivo `main.go` como punto de entrada de la aplicación:

```
.
├── CODEOWNERS
├── Dockerfile
├── go.mod
├── go.sum
├── internal
│   └── ...
├── package1
│   └── ...
├── package2
│   └── ...
├── main
│   └── main.go
├── okd
│   ├── deploy-image.yml
│   ├── deploy-params.env
│   ├── deploy-production-params.env
│   ├── development.yml
│   ├── production.yml
│   └── staging.yml
├── README.md
└─ sonar-project.properties
```

__Dockerfile__
```dockerfile
FROM registry.ar.bsch/santandertec/santander-tecnologia-docker-base-images-golang:v16

COPY my-api .

EXPOSE 8080

CMD [ "./my-api" ]
```

__sonar-project.properties__
```properties
sonar.projectKey=gitlab.ar.bsch/my-group/my-api
sonar.projectName=My API

sonar.exclusions=**/vendor/**, config/**/* ,docs/**/* ,resources/**/*

sonar.test.inclusions=**/*_test.go
sonar.test.exclusions=**/vendor/**, config/**/* ,docs/**/* ,resources/**/*
```

## Features no estandar

### Proyectos/pipelines modo librería

Para aquellos proyectos que consisten en packages que no compilan a un ejecutable sino que son librerías (como el toolkit: https://gitlab.ar.bsch/santander-tecnologia/santander-go-kit) existe un pipeline para dicho caso de uso, el cual cambia el stage de package

El mismo se habilita cambiando la siguiente variable en `.ci-variables-yml`:

```yaml
  PIPELINE_MODE_LIBRARY: "true"
```

### Soporte para makefiles

Por defecto los proyectos se buildean usando el comando de go nativo, `go build [...]`. Para casos que necesiten logica o pasos adicionales, se permite la posibilidad de ejecutar el build mediante makefiles. El stage de package va ejecutar el comando `make`, el cual defaultea a `make build`

Esto se habilita cambiando la siguiente variable en `.ci-variables-yml`:

```yaml
  USE_MAKEFILE: "true"
```

### Soporte para plugins

El pipeline es compatible con aquellos proyectos que deseen usar plugins (https://golang.org/pkg/plugin/) debiendo cumplir solamente con 2 requisitos:
 * Los modulos compilados (*.so) deben ubicarse en un directorio llamado `plugins_build`, en el root del proyecto
 * Durante la generacion de la imagen de docker, copiar los modulos anteriormente mencionados. Se puede realizar de la siguiente forma en el Dockerfile del proyecto:

```dockerfile
RUN mkdir -p ./plugins_build
ADD plugins_build ./plugins_build
```