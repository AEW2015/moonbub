#include <stdio.h>
#include "driver/spi_master.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_err.h"
void app_main(void) {
  gpio_config_t outputs = {.pin_bit_mask=(1ULL<<12)|(1ULL<<13), .mode=GPIO_MODE_OUTPUT};
  ESP_ERROR_CHECK(gpio_config(&outputs));
  gpio_set_level(12,1); gpio_set_level(13,1); vTaskDelay(pdMS_TO_TICKS(1));
  gpio_set_level(13,0); vTaskDelay(pdMS_TO_TICKS(5)); gpio_set_level(13,1); vTaskDelay(pdMS_TO_TICKS(5));
  spi_bus_config_t bus = {.mosi_io_num=10, .miso_io_num=-1, .sclk_io_num=11, .quadwp_io_num=-1, .quadhd_io_num=-1, .max_transfer_sz=32768};
  ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST,&bus,SPI_DMA_CH_AUTO));
  spi_device_interface_config_t dev = {.clock_speed_hz=5000000,.mode=0,.spics_io_num=-1,.queue_size=1,.flags=SPI_DEVICE_HALFDUPLEX};
  spi_device_handle_t handle;
  ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST,&dev,&handle));
  // First ILI9806E write: 0xff and FF 98 06 04 01 packed as 9-bit words.
  const unsigned char data[] = {0x7f,0xff,0xf3,0x10,0x68,0x24,0x04};
  spi_transaction_t t={.length=sizeof(data)*8,.tx_buffer=data};
  puts("PROBE_BEFORE_SPI2_LCD"); fflush(stdout);
  gpio_set_level(12,0); esp_err_t err=spi_device_polling_transmit(handle,&t); gpio_set_level(12,1);
  printf("PROBE_AFTER_SPI2_LCD error=%s\n",esp_err_to_name(err)); fflush(stdout);
}
