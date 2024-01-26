const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
  50, 1, 0.00001, 100000
);

camera.position.z = -7;
camera.position.y = 3;
camera.lookAt(10, 0, 0)

const canvas = document.getElementById('viewport3d');
const renderer = new THREE.WebGLRenderer({
  canvas: canvas, 
  antialias: true
});
renderer.setClearColor("#F9FAFB");

renderer.setSize(canvas.parentElement.offsetWidth, canvas.parentElement.offsetHeight);

const gridHelper = new THREE.GridHelper(24, 6, "#EAECF0", "#EAECF0");
scene.add( gridHelper );

const axesHelper = new THREE.AxesHelper( 1 );
scene.add( axesHelper );

// const oak = new THREE.PerspectiveCamera( 50, 16/9, -0.00001, -1 );
// const helper = new THREE.CameraHelper( oak );
// scene.add( helper );

const controls = new THREE.OrbitControls( camera, renderer.domElement );

var ambientLight = new THREE.AmbientLight( 0x404040 ); // soft white light
scene.add( ambientLight );

var directionalLight = new THREE.DirectionalLight( 0xffffff, 5 );
directionalLight.position.set( 10, 10, 10 ); // change the position as needed
scene.add( directionalLight );

var model;

var loader = new THREE.GLTFLoader();

      // Load a GLTF resource
      loader.load(
        // resource URL
        'oak-d-pro.glb',
        // called when the resource is loaded
        function ( gltf ) {

          model = gltf.scene;

          // Make the model bigger
          model.scale.set(6, 6, 6);  // Increase scale of the model
          // model.position.x = 1
          // model.rotation.y = 180

          scene.add( model );

        },
        // called while loading is progressing
        function ( xhr ) {

          console.log( ( xhr.loaded / xhr.total * 100 ) + '% loaded' );

        },
        // called when loading has errors
        function ( error ) {

          console.log( 'An error happened' );

        }
      );

controls.update();
const resizeObserver = new ResizeObserver((entries) => {
  for (let entry of entries) {
    if (entry.target === canvas.parentElement) {
      const cont = document.getElementById("canvas")
      const width = cont.offsetWidth;
      const height = cont.offsetHeight - 158;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }
  }
});

resizeObserver.observe(canvas.parentElement);


const geometry = new THREE.BufferGeometry();

// itemSize = 3 because there are 3 values (components) per vertex
//geometry.setAttribute( 'position', new THREE.BufferAttribute( vertices, 3 ) );
//geometry.setAttribute( 'color', new THREE.BufferAttribute( colors, 3 ) );
//const meshMaterial = new THREE.MeshBasicMaterial( { color: 0xff0000, wireframe: true } );
const meshMaterial = new THREE.MeshBasicMaterial( { color: 0xff0000, wireframe: false, vertexColors: true } );
const mesh = new THREE.Mesh( geometry, meshMaterial );
mesh.frustumCulled = false;

const pointsMaterial = new THREE.PointsMaterial({size: 0.07, sizeAttenuation: true, vertexColors: true});
const pointcloud = new THREE.Points( geometry, pointsMaterial );

pointcloud.frustumCulled = false;

scene.add(pointcloud);

const animate = () => {
  setTimeout(() => {
    window.requestAnimationFrame(animate);
  }, 1000 / 60 );
  renderer.render(scene, camera);
};
animate();

async function getPointCloudData() {
  const response = await fetch(`http://${window.location.hostname}:38154/pointcloud`);
  const buffer = await response.arrayBuffer();

  const numPoints = buffer.byteLength / 24;

  const pointcloud = new Float32Array(buffer);

  const positions = pointcloud.subarray(0, numPoints * 3);
  const colors = pointcloud.subarray(numPoints * 3);
  
  return {
    positions,
    colors,
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const startPointcloud = async () => {
    try {
        data = await getPointCloudData();
        geometry.setAttribute('position', new THREE.BufferAttribute(data.positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(data.colors, 3));
        geometry.attributes.position.needsUpdate = true;
        geometry.attributes.color.needsUpdate = true;
    } catch {
      sleep(1000)
    }
    sleep(1000/20);
    startPointcloud();
}

let offsetx = 0
let offsety = 0
let offsetz = 0
let updateoffset = false

const doIMU = async () => {
  //const url = "https:://robot-c38cf81f-e91b-46b5-b73f-b25c3bed60de.1-robothub.net/files/a66054c1-d02b-4520-90c2-1c6685568049/test.txt"
  try {
  //const uri = `/files/${robothubApi.robotAppId}/test.txt`
  response = await fetch(`http://${window.location.hostname}:38155/imu`).then(resp => resp.json())
  //console.error("RESP", response.yaw, response.pitch, response.roll)
  if (updateoffset) {
    offsetx = -response.pitch
    offsety = -response.roll
    offsetz = -response.yaw
    updateoffset = false
  }
  model.rotation.x = response.pitch + offsetx
  model.rotation.y = response.roll + offsety
  model.rotation.z = response.yaw + offsetz
  pointcloud.rotation.x = response.pitch + offsetx
  pointcloud.rotation.y = response.roll + offsety
  pointcloud.rotation.z = response.yaw + offsetz
  //model.rotation.z = response.roll
  } catch {}
  sleep(1000);
  doIMU();
  }