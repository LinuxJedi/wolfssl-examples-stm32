/**
  ******************************************************************************
  * File Name          : wolfSSL.I-CUBE-wolfTPM_conf.h
  * Description        : This file provides code for the configuration
  *                      of the wolfSSL.I-CUBE-wolfTPM_conf.h instances.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __WOLFSSL_I_CUBE_WOLFTPM_CONF_H__
#define __WOLFSSL_I_CUBE_WOLFTPM_CONF_H__

#ifdef __cplusplus
 extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/

/**
	MiddleWare name : wolfSSL.I-CUBE-wolfTPM.3.8.0
	MiddleWare fileName : ./wolfSSL.I-CUBE-wolfTPM_conf.h
	MiddleWare version :
*/
/*---------- WOLFTPM_CONF_WOLFCRYPT -----------*/
#define WOLFTPM_CONF_WOLFCRYPT      1

/*---------- WOLFTPM_CONF_HW_SPI -----------*/
#define WOLFTPM_CONF_HW_SPI      0

/*---------- WOLFTPM_CONF_DEBUG -----------*/
#define WOLFTPM_CONF_DEBUG      0

/*---------- WOLFTPM_CONF_SMALL_STACK -----------*/
#define WOLFTPM_CONF_SMALL_STACK      0

/*---------- WOLFTPM_CONF_TRANSPORT -----------*/
#define WOLFTPM_CONF_TRANSPORT      0

/* ------------------------------------------------------------------------- */
/* Platform */
/* ------------------------------------------------------------------------- */
#define NO_FILESYSTEM
#define NO_MAIN_DRIVER
#define WOLFTPM_EXAMPLE_HAL

/* Set smaller default timeout for embedded devices */
#define TPM_TIMEOUT_TRIES 10000000

/* Example for TPM wait delay */
#if 0
    #define XTPM_WAIT() HAL_Delay(1)
#endif

/* ------------------------------------------------------------------------- */
/* Enable Features */
/* ------------------------------------------------------------------------- */
#undef WOLFTPM2_NO_WOLFCRYPT
#if defined(WOLFTPM_CONF_WOLFCRYPT) && WOLFTPM_CONF_WOLFCRYPT == 0
    #define WOLFTPM2_NO_WOLFCRYPT
#endif

#undef USE_HW_SPI_CS
#if defined(WOLFTPM_CONF_HW_SPI) && WOLFTPM_CONF_HW_SPI == 1
    #define USE_HW_SPI_CS
#endif

/* Small stack support */
#if defined(WOLFTPM_CONF_SMALL_STACK) && WOLFTPM_CONF_SMALL_STACK == 1
    #define WOLFTPM_SMALL_STACK
    #define MAX_COMMAND_SIZE    1024
    #define MAX_RESPONSE_SIZE   1350
    #define WOLFTPM2_MAX_BUFFER 1500
    #define MAX_DIGEST_BUFFER   973
#endif

/* ------------------------------------------------------------------------- */
/* Hardware */
/* ------------------------------------------------------------------------- */

/* Interface Selection SPI or I2C */
/* 0=SPI, 1=I2C */
#if defined(WOLFTPM_CONF_TRANSPORT) && WOLFTPM_CONF_TRANSPORT == 0
    /* SPI (default) */
#elif defined(WOLFTPM_CONF_TRANSPORT) && WOLFTPM_CONF_TRANSPORT == 1
    #define WOLFTPM_I2C
    #define WOLFTPM_ADV_IO
#endif

/* TPM Hardware Type (default automatic detect) */
#if 0
    #define WOLFTPM_AUTODETECT
#else
    //#define WOLFTPM_SLB9670   /* Infineon */
    //#define WOLFTPM_SLB9672   /* Infineon */
    //#define WOLFTPM_MICROCHIP /* ATTPM20 */
    #define WOLFTPM_ST33      /* STM */
    //#define WOLFTPM_NUVOTON   /* NPCT75x */
#endif

/* Example STM32 SPI Hal Configuration */
#if 1
    /* Use PD14 for SPI1 CS */
    #define USE_SPI_CS_PORT GPIOA
    #define USE_SPI_CS_PIN  0
#endif

/* ------------------------------------------------------------------------- */
/* Debugging */
/* ------------------------------------------------------------------------- */
#if defined(WOLFTPM_CONF_DEBUG) && WOLFTPM_CONF_DEBUG == 1
    #define DEBUG_WOLFTPM
    //#define WOLFTPM_DEBUG_TIMEOUT
    //#define WOLFTPM_DEBUG_VERBOSE
    //#define WOLFTPM_DEBUG_IO
#endif

#ifdef __cplusplus
}
#endif
#endif /* WOLFSSL_I_CUBE_WOLFTPM_CONF_H_H */

/**
  * @}
  */

/*****END OF FILE****/
