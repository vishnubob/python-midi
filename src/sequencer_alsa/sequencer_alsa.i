%module sequencer_alsa
%feature("typemaps");
%feature("newobject");

%{
#include "include/seq_event.h"

#include <alsa/asoundlib.h>

snd_seq_t*
open_client(const char *name, const char *type, int stream, int mode)
{
    snd_seq_t *handle;
    int err;
    err = snd_seq_open(&handle, type, stream, mode);
    if (err < 0)
    {
            /* XXX: set global error */
            return NULL;
    }
    snd_seq_set_client_name(handle, name);
    return handle;
}

int
init_queue_tempo(snd_seq_t *handle, int queue, int bpm, int ppq)
{
    snd_seq_queue_tempo_t *tempo;
    snd_seq_queue_tempo_alloca(&tempo);
    snd_seq_queue_tempo_set_tempo(tempo, bpm);
    snd_seq_queue_tempo_set_ppq(tempo, ppq);
    return snd_seq_set_queue_tempo(handle, queue, tempo);
}

snd_seq_event_t*
event_input(snd_seq_t *handle)
{
    int err;
    snd_seq_event_t *ev;
    err = snd_seq_event_input(handle, &ev);
    if (err < 0)
    {
        /* XXX: does SWIG prevent us from raising an exception? */
        /* PyErr_SetString(PyExc_IOError, snd_strerror(err)); */
        return NULL;
    }
    return ev;
}

int snd_seq_control_queue_eventless(snd_seq_t *handle, 
        int queue, int type, int value)   
{
    return snd_seq_control_queue(handle, queue, type, value, NULL);
}


static PyObject *
client_poll_descriptors(snd_seq_t *handle)
{
    PyObject *ret;
    int npfd, idx;
    struct pollfd *pfd;
    npfd = snd_seq_poll_descriptors_count(handle, POLLIN);
    pfd = (struct pollfd *)calloc(npfd,  sizeof(struct pollfd));
    snd_seq_poll_descriptors(handle, pfd, npfd, POLLIN);

    ret = PyList_New(0);
    for (idx = 0; idx < npfd; idx++)
    {
        PyList_Append(ret, PyInt_FromLong((long)(pfd[idx].fd)));
    }
    free(pfd);
    return ret;
}
        
snd_seq_queue_status_t*
new_queue_status(snd_seq_t *handle, int queue)
{
    snd_seq_queue_status_t *qstatus;
    int err;
    err = snd_seq_queue_status_malloc(&qstatus);
    if (err < 0){
        return NULL;
    }
    return qstatus;
}

void
free_queue_status(snd_seq_queue_status_t *qstatus)
{
    snd_seq_queue_status_free(qstatus);
}

snd_seq_client_info_t*
new_client_info(void)
{
    snd_seq_client_info_t *cinfo;
    int err;
    err = snd_seq_client_info_malloc(&cinfo);
    if (err < 0){
        return NULL;
    }
    return cinfo;
}

snd_seq_port_info_t*
new_port_info(void)
{
    snd_seq_port_info_t *pinfo;
    int err;
    err = snd_seq_port_info_malloc(&pinfo);
    if (err < 0){
        return NULL;
    }
    return pinfo;
}

snd_seq_port_subscribe_t*
new_port_subscribe(void)
{
    snd_seq_port_subscribe_t *subs;
    int err;
    err = snd_seq_port_subscribe_malloc(&subs);
    if (err < 0){
        return NULL;
    }
    return subs;
}
%}

snd_seq_t *open_client(const char *name, const char *type, int stream, int mode);

snd_seq_port_subscribe_t *new_port_subscribe();

snd_seq_queue_status_t *new_queue_status(snd_seq_t *handle, int queue);
void free_queue_status(snd_seq_queue_status_t *qstatus);

snd_seq_port_info_t *new_port_info();

snd_seq_client_info_t *new_client_info();

snd_seq_event_t *event_input(snd_seq_t *handle);
int snd_seq_control_queue_eventless(snd_seq_t *handle, int queue, int type, int value);
int init_queue_tempo(snd_seq_t *handle, int queue, int bpm, int ppq);
PyObject *client_poll_descriptors(snd_seq_t *handle);

%typemap(out) ssize_t { $result = PyInt_FromLong($1); }
%typemap(in) ssize_t { $1 = PyInt_AsLong($input); }

// ignores from seq.h
%ignore snd_seq_system_info_sizeof;
%ignore snd_seq_system_info_malloc;
%ignore snd_seq_system_info_free;
%ignore snd_seq_system_info_copy;

%ignore snd_seq_client_info_sizeof;
%ignore snd_seq_client_info_malloc;
%ignore snd_seq_client_info_free;
%ignore snd_seq_client_info_copy;

%ignore snd_seq_client_info_get_broadcast_filter;
%ignore snd_seq_client_info_get_error_bounce;
%ignore snd_seq_client_info_get_event_filter;

%ignore snd_seq_client_info_set_broadcast_filter;
%ignore snd_seq_client_info_set_error_bounce;
%ignore snd_seq_client_info_set_event_filter;

%ignore snd_seq_client_info_event_filter_clear;
%ignore snd_seq_client_info_event_filter_add;
%ignore snd_seq_client_info_event_filter_del;
%ignore snd_seq_client_info_event_filter_check;

%ignore snd_seq_client_pool_malloc;
%ignore snd_seq_client_pool_free;
%ignore snd_seq_client_pool_copy;

%ignore snd_seq_client_pool_get_client;
%ignore snd_seq_client_pool_get_output_pool;
%ignore snd_seq_client_pool_get_input_pool;
%ignore snd_seq_client_pool_get_output_room;
%ignore snd_seq_client_pool_get_output_free;
%ignore snd_seq_client_pool_get_input_free;
%ignore snd_seq_client_pool_set_output_pool;
%ignore snd_seq_client_pool_set_input_pool;
%ignore snd_seq_client_pool_set_output_room;

%ignore snd_seq_get_client_pool;
%ignore snd_seq_set_client_pool;

%ignore snd_seq_port_info_sizeof;
%ignore snd_seq_port_info_malloc;
%ignore snd_seq_port_info_free;
%ignore snd_seq_port_info_copy;

%ignore snd_seq_port_subscribe_sizeof;
%ignore snd_seq_port_subscribe_malloc;
%ignore snd_seq_port_subscribe_free;
%ignore snd_seq_port_subscribe_copy;

%ignore snd_seq_query_subscribe_sizeof;
%ignore snd_seq_query_subscribe_malloc;
%ignore snd_seq_query_subscribe_free;
%ignore snd_seq_query_subscribe_copy;

%ignore snd_seq_query_subscribe_get_client;
%ignore snd_seq_query_subscribe_get_port;
%ignore snd_seq_query_subscribe_get_root;
%ignore snd_seq_query_subscribe_get_type;
%ignore snd_seq_query_subscribe_get_index;
%ignore snd_seq_query_subscribe_get_num_subs;
%ignore snd_seq_query_subscribe_get_addr;
%ignore snd_seq_query_subscribe_get_queue;
%ignore snd_seq_query_subscribe_get_exclusive;
%ignore snd_seq_query_subscribe_get_time_update;
%ignore snd_seq_query_subscribe_get_time_real;

%ignore snd_seq_query_subscribe_set_client;
%ignore snd_seq_query_subscribe_set_port;
%ignore snd_seq_query_subscribe_set_root;
%ignore snd_seq_query_subscribe_set_type;
%ignore snd_seq_query_subscribe_set_index;

%ignore snd_seq_query_port_subscribers;


%ignore snd_seq_queue_info_sizeof;
%ignore snd_seq_queue_info_malloc;
%ignore snd_seq_queue_info_free;
%ignore snd_seq_queue_info_copy;

%ignore snd_seq_queue_info_get_queue;
%ignore snd_seq_queue_info_get_name;
%ignore snd_seq_queue_info_get_owner;
%ignore snd_seq_queue_info_get_locked;
%ignore snd_seq_queue_info_get_flags;

%ignore snd_seq_queue_info_set_name;
%ignore snd_seq_queue_info_set_owner;
%ignore snd_seq_queue_info_set_locked;
%ignore snd_seq_queue_info_set_flags;

%ignore snd_seq_create_queue;
// %xx  ignore snd_seq_alloc_named_queue;
%ignore snd_seq_alloc_queue;
%ignore snd_seq_free_queue;
%ignore snd_seq_get_queue_info;
%ignore snd_seq_set_queue_info;
%ignore snd_seq_query_named_queue;

%ignore snd_seq_get_queue_usage;
%ignore snd_seq_set_queue_usage;


%ignore snd_seq_queue_status_sizeof;
%ignore snd_seq_queue_status_malloc;
%ignore snd_seq_queue_status_free;
%ignore snd_seq_queue_status_copy;

%ignore snd_seq_queue_status_get_queue;
%ignore snd_seq_queue_status_get_events;
%ignore snd_seq_queue_status_get_tick_time;
%ignore snd_seq_queue_status_get_real_time;
%ignore snd_seq_queue_status_get_status;

%ignore snd_seq_get_queue_status;


%ignore snd_seq_queue_tempo_sizeof;
%ignore snd_seq_queue_tempo_malloc;
%ignore snd_seq_queue_tempo_free;
%ignore snd_seq_queue_tempo_copy;

%ignore snd_seq_queue_tempo_get_queue;
%ignore snd_seq_queue_tempo_get_tempo;
%ignore snd_seq_queue_tempo_get_ppq;
%ignore snd_seq_queue_tempo_get_skew;
%ignore snd_seq_queue_tempo_get_skew_base;
%ignore snd_seq_queue_tempo_set_tempo;
%ignore snd_seq_queue_tempo_set_ppq;
%ignore snd_seq_queue_tempo_set_skew;
%ignore snd_seq_queue_tempo_set_skew_base;

%ignore snd_seq_get_queue_tempo;
%ignore snd_seq_set_queue_tempo;


// ignores from seqmid.h
%ignore snd_seq_set_client_pool_output;
%ignore snd_seq_set_client_pool_output_room;
%ignore snd_seq_set_client_pool_input;

// ignores from seq_event.h


// ignores from seq_midi_event.h
%ignore snd_midi_event_new;
%ignore snd_midi_event_resize_buffer;
%ignore snd_midi_event_free;
%ignore snd_midi_event_init;
%ignore snd_midi_event_reset_encode;
%ignore snd_midi_event_reset_decode;
%ignore snd_midi_event_no_status;
%ignore snd_midi_event_encode;
%ignore snd_midi_event_encode_byte;
%ignore snd_midi_event_decode;



%include "include/seq.h"
%include "include/seqmid.h"
%include "include/seq_event.h"
%include "include/seq_midi_event.h"
%include "include/error.h"

