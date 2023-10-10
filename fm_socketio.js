

http = require('http');
cloudcmd = require('cloudcmd');
Server = require('socket.io').Server;
express = require('express');
const serveIndex = require('serve-index')


const app = express();
const port = 3000;

const http_server = http.createServer(app);
const prefix = '/fm'

const io = require('socket.io')(http_server);
const socket = new Server(http_server, {
    path: `${prefix}/socket.io`,
});

const config = {
    name: 'cloudcmd :)',
    root: "\\",
};

const filePicker = {
    data: {
        FilePicker: {
            key: 'key',
        },
    },
};

// override option from json/modules.json
const modules = {
    filePicker,
};

const {
    createConfigManager,
    configPath,
} = cloudcmd;

const configManager = createConfigManager({
    configPath,
});



app.use(prefix, cloudcmd({
    socket, // used by Config, Edit (optional) and Console (required)
    config, // config data (optional)
    modules, // optional
    configManager, // optional
}));



app.get('/', function(req, res){
        res.sendFile(__dirname + '/client_gui.html');
});

app.use('/log', express.static('log'), serveIndex('log', {'icons': true}))
app.use('/image', express.static('image'), serveIndex('image', {'icons': true}))


io.on('connection', function(socket){
   // console.log('A user connected');
   updatelog('A user connected');
   
   // Send a message when
   socket.on('disconnect', function () {
        // console.log('A user disconnected');
        updatelog('A user disconnected');
   });
   socket.on('msg_engine', (data)=>{
        socket.broadcast.emit("msg_engine_status", data);
        // console.log(data);
        updatelog("[msg_engine] ---> [msg_engine_status]");
    });

   socket.on('msg_gui', (data)=>{
        socket.broadcast.emit("msg_gui", data);
        // console.log(data);
        updatelog("[msg_gui] <--- [msg_gui]");
    });

});





http_server.listen(port, function(){
   // console.log('listening on localhost:3000');
	updatelog(`listening on localhost:${port}`);
});

setTimeout(()=>{console.log(`listening on localhost:${port}`)}, 2000)

function updatelog(text){
    now = new Date().toISOString();
    console.log(now + " " + text);
}
