%module sequencer_alsa
%feature("typemaps");
%feature("newobject");

%{
#include <alsa/seq_event.h>
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

#define __attribute__(x) 

%include alsa/seq.h
%include alsa/seqmid.h
%include alsa/seq_event.h
%include alsa/seq_midi_event.h
%include alsa/error.h
