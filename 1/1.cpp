/**
 * PrimeTime
 *
 * Protohackers challenge
 *
 * March 31st, 2026
 **/
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <signal.h>

#include <iostream>
#include <thread>
#include <nlohmann/json.hpp>

#define PORT "7007"
#define BACKLOG 5

using json = nlohmann::json;

bool is_prime_i(int n) {
    if (n < 2) {
        return false;
    }
    // Check if N is divisible by any number between 1 and sqrt(N)
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) {
            return false;
        }
    }
    return true;
}

bool is_prime(double n) {
    if (n != (int)n) {
        return false;
    }
    return is_prime_i((int)n);
}

void sigchld_handler(int s) {
    (void)s; // quiet unused variable warning

    // waitpid() might overwrite errno, so we save and restore it:
    int saved_errno = errno;

    while(waitpid(-1, NULL, WNOHANG) > 0);

    errno = saved_errno;
}

// get sockaddr, IPv4 or IPv6:
void *get_in_addr(struct sockaddr *sa) {
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in*)sa)->sin_addr);
    }

    return &(((struct sockaddr_in6*)sa)->sin6_addr);
}

void send_failure(int file_desc) {
    std::cout << "SENDING BAD RESPONSE!\n"<< std::endl;
    std::string bad_response = "Bad request!\n";
    send(file_desc, bad_response.c_str(), bad_response.length(), 0);
    close(file_desc);
    return;
}

void serve_client(int file_desc) {

    char buf[1024];
    
    while (1) {
        memset(buf, 0, 1024);

        int bytes_received;
        if ((bytes_received = recv(file_desc, buf, 1024, 0)) == -1) {
            perror("send");
        }

        if (bytes_received == 0) {
            send_failure(file_desc);
            return;
        }

        std::string buf_s{buf};
        json j_request;

        try {
            j_request = json::parse(buf_s);
            std::cout << "RECEIVED:" << j_request << "\n";
            bool has_keys = j_request.contains("method") && j_request.contains("number");
            if (!has_keys) {
                send_failure(file_desc);
                return;
            }
            bool right_method = j_request["method"] == "isPrime";
            if (!right_method) {
                send_failure(file_desc);
                return;
            }
            bool proper_types = 
                (j_request["number"].type() == json::value_t::number_integer) ||
                (j_request["number"].type() == json::value_t::number_unsigned) ||
                (j_request["number"].type() == json::value_t::number_float);
            if (!proper_types) {
                send_failure(file_desc);
                return;
            }
        } catch (nlohmann::json::parse_error) {
            std::cout << "parse error" << std::endl;
            send_failure(file_desc);
            return;
        }

        using namespace nlohmann::literals;

        json j_response = {
            {"method", "isPrime"},
            {"prime", is_prime(j_request["number"])}
        };

        std::string buf_re = j_response.dump() + "\n";

        std::cout << "SENDING:" << buf_re << std::endl;

        send(file_desc, buf_re.c_str(), buf_re.length(), 0);
    }
}

int main(void) {
    // listen on sock_fd, new connection on new_fd
    int sockfd, new_fd;
    struct addrinfo hints, *servinfo, *p;
    struct sockaddr_storage their_addr; // connector's address info
    socklen_t sin_size;
    struct sigaction sa;
    int yes=1;
    char s[INET6_ADDRSTRLEN];
    int rv;

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE; // use my IP

    if ((rv = getaddrinfo(NULL, PORT, &hints, &servinfo)) != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        return 1;
    }

    // loop through all the results and bind to the first we can
    for(p = servinfo; p != NULL; p = p->ai_next) {
        if ((sockfd = socket(p->ai_family, p->ai_socktype,
                p->ai_protocol)) == -1) {
            perror("server: socket");
            continue;
        }

        if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes,
                sizeof(int)) == -1) {
            perror("setsockopt");
            exit(1);
        }

        if (bind(sockfd, p->ai_addr, p->ai_addrlen) == -1) {
            close(sockfd);
            perror("server: bind");
            continue;
        }

        break;
    }

    freeaddrinfo(servinfo); // all done with this structure

    if (p == NULL)  {
        fprintf(stderr, "server: failed to bind\n");
        exit(1);
    }

    if (listen(sockfd, BACKLOG) == -1) {
        perror("listen");
        exit(1);
    }

    sa.sa_handler = sigchld_handler; // reap all dead processes
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    if (sigaction(SIGCHLD, &sa, NULL) == -1) {
        perror("sigaction");
        exit(1);
    }

    printf("server: waiting for connections...\n");

    std::vector<std::thread*> workers;

    while(1) {  // main accept() loop
        sin_size = sizeof their_addr;
        new_fd = accept(sockfd, (struct sockaddr *)&their_addr,
            &sin_size);
        if (new_fd == -1) {
            perror("accept");
            continue;
        }

        inet_ntop(their_addr.ss_family,
            get_in_addr((struct sockaddr *)&their_addr),
            s, sizeof s);
        printf("server: got connection from %s\n", s);

        std::thread worker(serve_client, new_fd);
        workers.push_back(&worker);
        worker.detach();
    }

    close(sockfd);

    return 0;
}