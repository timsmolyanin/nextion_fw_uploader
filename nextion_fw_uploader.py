import serial
import time
import codecs
import struct
from math import ceil


def connect(com, baud):
    """
    Метод создает объект соединения и сразу открывает СОМ-порт
    :return: True/False, в зависимости от того, удалось ли открыть указанный СОМ-порт
    """
    print("Connect to COM-port")
    serial_port_open_flag = False
    serial_port = None
    while not serial_port_open_flag:
        time.sleep(1)
        try:
            serial_port = serial.Serial(port=com,
                                        baudrate=baud,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout=1)

            serial_port_open_flag = serial_port.isOpen()
        except serial.serialutil.SerialException as exc:
            # TODO: log error
            print(exc)
            serial_port_open_flag = False

        return [serial_port_open_flag, serial_port]

def serial_write(sp, cmd, nenc):
    """
    Метод для записи в COM-порт команд для Nextion

    TODO:
    - структура команд
    - если серийный порт закрыт, то чего тогда?
    - если данные без терминатора, то чего тогда?
    -
    :return:
    """

    eof = struct.pack('B', 0xff)
    try:
        if nenc:
            sp.write(cmd)
            sp.write(eof)
            sp.write(eof)
            sp.write(eof)
        else:
            sp.write(cmd.encode())
            sp.write(eof)
            sp.write(eof)
            sp.write(eof)
    except Exception as exc:
        print("Exception while serial_write method.", exc)

def serial_read(st, com):
    """
    Метод, который осуществляет постоянное чтение COM-порта.
    Происходит проверка открыт ли порт, если да, то читаем данные с порта,
    исключаем пустые строки, которые Nextion шлет каждую секунду,
    исключаем данные без терминатора /r/n, т.к. все валидные данные с Nextion должны его содержать,
    и если все хорошо - выдаем данные в callback функцию для дальнейшей обработки.
    Структура данных принимаемых с Nextion:

    !ВОЗМОЖНЫ ИЗМЕНЕНИЯ!

    aaa.bbb.ccc/r/n
    aaa - [electric, light, temperature, water]
    bbb - совпадает с MQTT топиком, example - OutletGroup1
    ccc - ON/OF, чего-то такое
    :return:

    TODO:
    - если серийный порт закрыт, то чего тогда?
    - если данные без терминатора, то чего тогда?
    -
    """
    if not st:
        print('vsdvsdvsd')
    response = ""
    try:
        response = com.readline()
        if response == b'':
            print(response)
            # Nextion send empty string every second
            pass
        else:
            print('Response data from Nextion: ', response)
    except Exception as exc:
        print("Exception while serial_read method.", exc)


def get_firmware_size():
    with open('test.tft', "rb") as f:
        f.seek(0x3c)
        rawSize = f.read(struct.calcsize("<I"))
    fileSize = struct.unpack("<I", rawSize)[0]
    return fileSize


def main():
    fw_size = None
    serial_port = None
    st = None
    NXSKP = b"\x08"

    print('1. Попытка подключения к COM порту')
    serail_list = connect('COM4', 115200)
    print(serail_list)
    if serail_list[0]:
        st = serail_list[0]
        serial_port = serail_list[1]
    
    print('2. Поучение размера прошивки')
    fw_size = get_firmware_size()
    print(fw_size)

    print('3. Отправляем инструкцию "connect"')
    serial_write(serial_port, 'connect', False)
    serial_read(st, serial_port)

    serial_write(serial_port, "", False)
    serial_read(st, serial_port)

    print('4. Отправляем информацию о прошивке')
    whmi_wri = f'whmi-wri {fw_size},115200,0'
    serial_write(serial_port, whmi_wri, False)
    serial_read(st, serial_port)

    print('4. Отправка прошивки')
    blockSize = 4096
    remainingBlocks = ceil(fw_size / blockSize)
    blocksSent, lastProgress, lastEta = 0, 0, 0

    with open('test.tft', "rb") as f:
        startTime = time.time()
        while remainingBlocks:
            serial_write(serial_port, f.read(blockSize), True)
            remainingBlocks -= 1
            blocksSent += 1
            
            proceed = serial_read(st, serial_port)
            if proceed == NXSKP:
                serial_read(st, serial_port)
                # if len(offset) != 4:
                #      raise Exception("Incomplete offset for skip command (0x08).")
                # offset = struct.unpack("<I", offset)[0]
                # if (offset):
                #     # A value of 0 doesn't mean "seek to position 0" but "don't seek anywhere".
                #     jumpSize = offset - f.tell()
                #     f.seek(offset)
                #     remainingBlocks = ceil((fw_size - offset) / blockSize)
                #     print("Skipped {} bytes.".format(jumpSize))
                # else:
                #     pass
                #     self.ack(proceed)

                # progress = 100 * f.tell() // fw_size
                # eta = ceil((time.time() - startTime) / blocksSent * remainingBlocks)
                # if progress != lastProgress or eta != lastEta:
                #     lastEta = eta
                #     lastProgress = progress
                #     eta = "{}m{:02}s".format(eta // 60, eta % 60)
                #     print("Progress: {}%  ETA: {}".format(progress, eta), end="\r")




if __name__ == '__main__':
    main()
    
"""
sendCommand("");
    waitForResponse();
    qDebug() << "Sending firmware info...";
    QByteArray whmi_wri = "whmi-wri ";
    whmi_wri += QString::number(firmware.size());
    whmi_wri += ",";
    whmi_wri += QString::number(serialUploadBaudrate);
    whmi_wri += ",0";
    sendCommand(whmi_wri);
    waitForResponse(2000);   // 0x05

    while(firmware.size())
    {
        qDebug().noquote().nospace()
                << "Remaing data: " << firmware.size()
                << " bytes (" << QString::number(100.-100.*firmware.size()/firmwareSize,'f',2) << "%)";
        QByteArray chunk = firmware.left(4096);
        serial.write(chunk);
        serial.waitForBytesWritten();
        firmware.remove(0,chunk.size());
        waitForResponse(1000);
"""