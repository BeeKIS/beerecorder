#! /usr/bin/env python3

from threading import Thread
import socket
from IPython import embed

def do_some_stuffs_with_input(input_string):
    """
    This is where all the processing happens.

    Let's just read the string backwards
    """

    print("Processing that nasty input!")
    return input_string[::-1]

#
# def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 4096):
#
#     # the input is in bytes, so decode it
#     input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)
#
#     # MAX_BUFFER_SIZE is how big the message can be
#     # this is test if it's sufficiently big
#     import sys
#     siz = sys.getsizeof(input_from_client_bytes)
#     if  siz >= MAX_BUFFER_SIZE:
#         print("The length of input is probably too long: {}".format(siz))
#
#     # decode input and strip the end of line
#     input_from_client = input_from_client_bytes.decode("utf8").rstrip()
#
#     res = do_some_stuffs_with_input(input_from_client)
#     print("Result of processing {} is: {}".format(input_from_client, res))
#
#     vysl = res.encode("utf8")  # encode the result string
#     conn.sendall(vysl)  # send it to client
#     conn.close()  # close connection
#     print('Connection ' + ip + ':' + port + " ended")


def rec_data(conn, MAX_BUFFER_SIZE):
    input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

    import sys
    siz = sys.getsizeof(input_from_client_bytes)
    if  siz >= MAX_BUFFER_SIZE:
        print("The length of input is probably too long: {}".format(siz))

    input_from_client = input_from_client_bytes.decode("utf8").rstrip()

    return input_from_client


def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 88888):

    # read lines periodically without ending connection
    still_listen = True
    count = 1
    while still_listen:
        input_from_client = rec_data(conn, MAX_BUFFER_SIZE)

        # if you receive this, end the connection
        if "--ENDOFDATA--" in input_from_client:
            print('--ENDOFDATA--')
            conn.close()
            print('Connection ' + ip + ':' + port + " ended")
            still_listen = False
        else:
            splin = input_from_client.split('\t')
            print("{}".format(splin[0]))
            # embed()
            # tell client that we can accept another data processing
            # conn.sendall("-".encode("utf8"))
            # conn.sendall("bla".encode("utf-8"))
            conn.send(b'17')
            count += 1
            print(count)



def start_server():

    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Socket created')

    try:
        soc.bind(("127.0.0.1", 12345))
        print('Socket bind complete')
    except socket.error as msg:
        import sys
        print('Bind failed. Error : ' + str(sys.exc_info()))
        sys.exit()

    #Start listening on socket
    soc.listen(10)
    print('Socket now listening')

    # this will make an infinite loop needed for
    # not reseting server for every client
    while True:
        conn, addr = soc.accept()
        ip, port = str(addr[0]), str(addr[1])
        print('Accepting connection from ' + ip + ':' + port)
        try:
            Thread(target=client_thread, args=(conn, ip, port)).start()
        except:
            print("Terible error!")
            import traceback
            traceback.print_exc()
    soc.close()

if __name__ == "__main__":
    start_server()


